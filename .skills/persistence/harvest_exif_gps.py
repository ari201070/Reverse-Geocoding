#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cosecha GPS EXIF nativo + Export JSON para portal Argentina 2025.
"""
import os, sys, sqlite3, io, json, piexif
from pathlib import Path
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ROOT = Path("F:/")

def dms_to_decimal(dms, ref):
    if not dms or len(dms) < 3: return None
    d = dms[0][0] / dms[0][1] if dms[0][1] else 0
    m = dms[1][0] / dms[1][1] if dms[1][1] else 0
    s = dms[2][0] / dms[2][1] if dms[2][1] else 0
    dec = d + m/60 + s/3600
    if ref in ("S", "W"): dec = -dec
    return round(dec, 6)

def read_exif_gps(filepath):
    try:
        ex = piexif.load(filepath)
        gps = ex.get("Exif", {})
        gps_ifd = ex.get("GPS", {})
        if not gps_ifd: return None, None

        lat_dms = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        lat_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
        lng_dms = gps_ifd.get(piexif.GPSIFD.GPSLongitude)
        lng_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)

        if not all([lat_dms, lat_ref, lng_dms, lng_ref]): return None, None
        lat = dms_to_decimal(lat_dms, lat_ref.decode() if isinstance(lat_ref, bytes) else lat_ref)
        lng = dms_to_decimal(lng_dms, lng_ref.decode() if isinstance(lng_ref, bytes) else lng_ref)
        if lat and lng and -90 <= lat <= 90 and -180 <= lng <= 180:
            return lat, lng
    except: pass
    return None, None

def read_exif_datetime(filepath):
    try:
        ex = piexif.load(filepath)
        raw = ex.get("Exif", {}).get(36867) or ex.get("Exif", {}).get(36868)
        if raw:
            dt = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else str(raw)
            return dt
    except: pass
    return None

def main():
    print(f"\n{'='*60}")
    print(f"  Cosecha EXIF GPS + Export JSON Argentina 2025")
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

    # Find candidates: location_source != VOUCHER_INHERITANCE and lat is NULL
    candidates = c.execute(
        "SELECT id, final_path, filename FROM photos WHERE (location_source IS NULL OR location_source != 'VOUCHER_INHERITANCE') AND (lat IS NULL OR lat = 0)"
    ).fetchall()
    print(f"\n  Candidatas a cosecha EXIF: {len(candidates)}")

    found_gps = 0
    found_dt = 0
    errors = 0
    batch = []
    batch_dt = []
    total = len(candidates)

    for i, (pid, fpath, fname) in enumerate(candidates):
        if i % 2000 == 0 and i > 0:
            print(f"    ...{i}/{total} ({found_gps} GPS, {found_dt} datetime, {errors} errores)")

        if not fpath or not Path(fpath).exists():
            errors += 1
            continue

        lat, lng = read_exif_gps(fpath)
        if lat is not None and lng is not None:
            found_gps += 1
            batch.append((lat, lng, "EXIF_GPS", pid))

        dt_str = read_exif_datetime(fpath)
        if dt_str:
            found_dt += 1
            batch_dt.append((dt_str, pid))

        if len(batch) >= 500:
            c.executemany("UPDATE photos SET lat=?, lng=?, location_source=? WHERE id=?", batch)
            conn.commit(); batch = []
        if len(batch_dt) >= 500:
            c.executemany("UPDATE photos SET date_taken=? WHERE id=?", batch_dt)
            conn.commit(); batch_dt = []

    if batch:
        c.executemany("UPDATE photos SET lat=?, lng=?, location_source=? WHERE id=?", batch)
        conn.commit()
    if batch_dt:
        c.executemany("UPDATE photos SET date_taken=? WHERE id=?", batch_dt)
        conn.commit()

    print(f"\n  [FASE 1] Cosecha EXIF completada:")
    print(f"    GPS nativo encontrado:    {found_gps}")
    print(f"    DateTimeOriginal grabado: {found_dt}")
    print(f"    Errores/archivos faltantes: {errors}")

    # --- FASE 2: Export JSON Argentina 2025 ---
    print(f"\n  [FASE 2] Exportando JSON Argentina 2025...")

    # Get all photos from October 2025 (Argentina trip)
    arg_photos = c.execute("""
        SELECT id, final_path, filename, lat, lng, date_taken, location_source, city
        FROM photos
        WHERE year = 2025 AND month_folder = '10-Octubre'
        ORDER BY date_taken ASC, id ASC
    """).fetchall()

    print(f"    Fotos Octubre 2025: {len(arg_photos)}")

    # Check for thumbs
    thumbs_dir = ROOT / "2025" / "Viaje Familiar de 30 dias por Argentina" / "_thumbs"
    has_thumbs = thumbs_dir.exists()

    export = []
    for pid, fpath, fname, lat, lng, dt, ls, city in arg_photos:
        # Build thumb path
        thumb_path = None
        if has_thumbs and fpath:
            # Try to find thumb by filename pattern
            fp = Path(fpath)
            thumb_candidate = thumbs_dir / f"thumb_{pid}.jpg"
            if thumb_candidate.exists():
                thumb_path = str(thumb_candidate.relative_to(ROOT.parent))

        export.append({
            "id": pid,
            "original_path": fpath,
            "thumb_path": thumb_path,
            "latitude": lat,
            "longitude": lng,
            "datetime_original": dt,
            "location_source": ls,
            "city": city
        })

    # Write JSON
    out_dir = ROOT / "2025" / "Octubre"
    out_path = out_dir / "argentina_metadata.json"
    with open(str(out_path), "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    print(f"    JSON exportado: {out_path}")
    print(f"    Registros: {len(export)}")

    # Final stats
    total_gps = c.execute("SELECT COUNT(*) FROM photos WHERE lat IS NOT NULL AND lat != 0").fetchone()[0]
    total_voucher = c.execute("SELECT COUNT(*) FROM photos WHERE location_source = 'VOUCHER_INHERITANCE'").fetchone()[0]
    total_exif = c.execute("SELECT COUNT(*) FROM photos WHERE location_source = 'EXIF_GPS' AND lat IS NOT NULL AND lat != 0").fetchone()[0]
    total_no_gps = c.execute("SELECT COUNT(*) FROM photos WHERE lat IS NULL OR lat = 0").fetchone()[0]
    conn.close()

    print(f"\n{'='*60}")
    print(f"  RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"  Total fotos en DB:        26,683")
    print(f"  Con GPS total:            {total_gps}")
    print(f"    - VOUCHER_INHERITANCE:  {total_voucher}")
    print(f"    - EXIF_GPS nativo:      {total_exif}")
    print(f"  Sin GPS:                  {total_no_gps}")
    print(f"  JSON Argentina 2025:      {len(export)} fotos exportadas")
    print(f"\n  [OK] DB + JSON actualizados")

if __name__ == "__main__":
    main()
