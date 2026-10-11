#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migracion photo_catalog.db: H3 Index + Date Recovery + Round Fix
"""
import os, sys, re, io, sqlite3, h3
from pathlib import Path
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

DATE_PATTERNS = [
    (r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2})[.:](\d{2})[.:](\d{2})", "%Y-%m-%d %H:%M:%S"),
    (r"(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})(\d{2})", "%Y-%m-%d %H:%M:%S"),
    (r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", "%Y-%m-%d %H:%M:%S"),
    (r"(\d{4})(\d{2})(\d{2})\s+(\d{2})(\d{2})(\d{2})", "%Y-%m-%d %H:%M:%S"),
    (r"(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})", "%Y-%m-%d %H:%M:%S"),
    (r"(\d{4})-(\d{2})-(\d{2})", "%Y-%m-%d 00:00:00"),
    (r"(\d{4})(\d{2})(\d{2})", "%Y-%m-%d 00:00:00"),
]

def round6(v):
    if v is None: return None
    return round(float(v), 6)

def extract_date_from_filename(fname):
    for pattern, fmt in DATE_PATTERNS:
        m = re.search(pattern, fname)
        if m:
            g = m.groups()
            try:
                if len(g) == 6:
                    dt_str = f"{g[0]}-{g[1]}-{g[2]} {g[3]}:{g[4]}:{g[5]}"
                elif len(g) == 3:
                    dt_str = f"{g[0]}-{g[1]}-{g[2]} 00:00:00"
                else:
                    continue
                datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                return dt_str
            except: continue
    return None

def read_exif_datetime(filepath):
    try:
        import piexif
        ex = piexif.load(filepath)
        raw = ex.get("Exif", {}).get(36867) or ex.get("Exif", {}).get(36868)
        if raw:
            dt = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else str(raw)
            m = re.match(r"(\d{4}):(\d{2}):(\d{2})\s+(\d{2}):(\d{2}):(\d{2})", dt)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}:{m.group(6)}"
    except: pass
    return None

def main():
    print(f"\n{'='*60}")
    print(f"  Migracion photo_catalog.db")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    c = conn.cursor()

    # === FASE 1: H3 Index ===
    print(f"\n  [FASE 1] H3 Index (Resolucion 9)...")

    existing_cols = {r[1] for r in c.execute("PRAGMA table_info(photos)").fetchall()}
    if "h3_index" not in existing_cols:
        c.execute("ALTER TABLE photos ADD COLUMN h3_index TEXT")
        print("    Columna h3_index agregada")
    if "date_source" not in existing_cols:
        c.execute("ALTER TABLE photos ADD COLUMN date_source TEXT")
        print("    Columna date_source agregada")
    conn.commit()

    gps_rows = c.execute("SELECT id, lat, lng FROM photos WHERE lat IS NOT NULL AND lat != 0").fetchall()
    print(f"    Fotos con GPS: {len(gps_rows)}")

    h3_batch = []
    for pid, lat, lng in gps_rows:
        try:
            h3_cell = h3.latlng_to_cell(round6(lat), round6(lng), 9)
            h3_batch.append((h3_cell, pid))
        except: pass

    c.executemany("UPDATE photos SET h3_index=? WHERE id=?", h3_batch)
    conn.commit()
    print(f"    Celdas H3 calculadas e inyectadas: {len(h3_batch)}")

    # === FASE 2: Date Recovery ===
    print(f"\n  [FASE 2] Recuperacion de fechas NULL...")

    null_dates = c.execute(
        "SELECT id, final_path, filename FROM photos WHERE date_taken IS NULL OR date_taken = ''"
    ).fetchall()
    print(f"    Fotos sin fecha: {len(null_dates)}")

    exif_count = 0
    fname_count = 0
    mtime_count = 0
    fail_count = 0
    date_batch = []

    for i, (pid, fpath, fname) in enumerate(null_dates):
        if i % 2000 == 0 and i > 0:
            print(f"    ...{i}/{len(null_dates)} (EXIF:{exif_count} Name:{fname_count} MTime:{mtime_count} Fail:{fail_count})")

        dt_str = None
        source = None

        # Paso A: EXIF
        if fpath and Path(fpath).exists():
            dt_str = read_exif_datetime(fpath)
            if dt_str:
                source = "EXIF"

        # Paso B: Filename
        if not dt_str and fname:
            dt_str = extract_date_from_filename(fname)
            if dt_str:
                source = "FILENAME"

        # Paso C: mtime
        if not dt_str and fpath and Path(fpath).exists():
            try:
                mt = os.path.getmtime(fpath)
                dt_str = datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M:%S")
                source = "MTIME"
            except: pass

        if dt_str:
            date_batch.append((dt_str, source, pid))
            if source == "EXIF": exif_count += 1
            elif source == "FILENAME": fname_count += 1
            elif source == "MTIME": mtime_count += 1
        else:
            fail_count += 1

        if len(date_batch) >= 500:
            c.executemany("UPDATE photos SET date_taken=?, date_source=? WHERE id=?", date_batch)
            conn.commit(); date_batch = []

    if date_batch:
        c.executemany("UPDATE photos SET date_taken=?, date_source=? WHERE id=?", date_batch)
        conn.commit()

    print(f"    EXIF:        {exif_count}")
    print(f"    Filename:    {fname_count}")
    print(f"    MTime:       {mtime_count}")
    print(f"    Sin exito:   {fail_count}")

    # === FASE 3: Round Fix ===
    print(f"\n  [FASE 3] Redondeo a 6 decimales...")

    coords_rows = c.execute(
        "SELECT id, lat, lng FROM photos WHERE lat IS NOT NULL AND lat != 0"
    ).fetchall()
    round_batch = []
    rounded_count = 0
    for pid, lat, lng in coords_rows:
        rlat, rlng = round6(lat), round6(lng)
        if rlat != lat or rlng != lng:
            rounded_count += 1
            # Recalcular H3 con coordenadas redondeadas
            try:
                h3_cell = h3.latlng_to_cell(rlat, rlng, 9)
            except:
                h3_cell = None
            round_batch.append((rlat, rlng, h3_cell, pid))

    c.executemany("UPDATE photos SET lat=?, lng=?, h3_index=? WHERE id=?", round_batch)
    conn.commit()
    print(f"    Coordenadas ajustadas: {rounded_count}")

    # === RESUMEN ===
    total = c.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    with_h3 = c.execute("SELECT COUNT(*) FROM photos WHERE h3_index IS NOT NULL").fetchone()[0]
    with_dt = c.execute("SELECT COUNT(*) FROM photos WHERE date_taken IS NOT NULL AND date_taken != ''").fetchone()[0]
    with_gps = c.execute("SELECT COUNT(*) FROM photos WHERE lat IS NOT NULL AND lat != 0").fetchone()[0]
    conn.close()

    print(f"\n{'='*60}")
    print(f"  RESUMEN MIGRACION")
    print(f"{'='*60}")
    print(f"  Total fotos:              {total}")
    print(f"  Con GPS:                  {with_gps}")
    print(f"  Con H3 index:             {with_h3}")
    print(f"  Con date_taken:           {with_dt}")
    print(f"  Fecha desde EXIF:         {exif_count}")
    print(f"  Fecha desde Filename:     {fname_count}")
    print(f"  Fecha desde MTime:        {mtime_count}")
    print(f"  Coordenadas redondeadas:  {rounded_count}")
    print(f"\n  [OK] Migracion completada")

if __name__ == "__main__":
    main()
