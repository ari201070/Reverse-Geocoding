#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Propagacion de coordenadas GPS desde Anclas Espacio-Temporales (Vouchers)
a fotos sin GPS en photo_catalog.db. Usa mtime del archivo como fallback.
"""
import os, sys, sqlite3, io
from pathlib import Path
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
DRY_RUN = "--dry-run" in sys.argv

ANCHORS = [
    {"id":"Hotel_Concorde_Bariloche","type":"hotel","start":"2025-10-05 14:00:00","end":"2025-10-10 10:00:00","lat":-41.1334,"lng":-71.3114,"city":"San Carlos de Bariloche","province":"Rio Negro","country":"Argentina"},
    {"id":"Sun_Moon_Rome","type":"hotel","start":"2023-10-02 15:59:00","end":"2023-10-05 09:59:00","lat":41.9023,"lng":12.5054,"city":"Roma","province":"Lacio","country":"Italia"},
    {"id":"Museo_Leonardo_da_Vinci_Rome","type":"activity","start":"2023-10-02 10:00:00","end":"2023-10-02 19:00:00","lat":41.8967,"lng":12.4716,"city":"Roma","province":"Lacio","country":"Italia"},
    {"id":"Capilla_Sixtina_Vaticano","type":"activity","start":"2023-10-03 14:30:00","end":"2023-10-03 18:30:00","lat":41.9069,"lng":12.4533,"city":"Ciudad del Vaticano","province":"Vaticano","country":"Vaticano"},
    {"id":"Pantheon_Rome","type":"activity","start":"2023-10-04 11:30:00","end":"2023-10-04 13:00:00","lat":41.8986,"lng":12.4769,"city":"Roma","province":"Lacio","country":"Italia"},
    {"id":"Colosseum_Forum_Tour","type":"activity","start":"2023-10-04 14:30:00","end":"2023-10-04 18:00:00","lat":41.8906,"lng":12.4906,"city":"Roma","province":"Lacio","country":"Italia"},
    {"id":"BB_Marbo_Florence","type":"hotel","start":"2023-10-05 13:30:00","end":"2023-10-09 10:59:00","lat":43.7781,"lng":11.2454,"city":"Florencia","province":"Toscana","country":"Italia"},
    {"id":"Pisa_Day_Trip","type":"activity","start":"2023-10-06 09:30:00","end":"2023-10-06 18:00:00","lat":43.7228,"lng":10.3948,"city":"Pisa","province":"Toscana","country":"Italia"},
    {"id":"Hotel_Soperga_Milan","type":"hotel","start":"2023-10-09 13:59:00","end":"2023-10-12 09:59:00","lat":45.4885,"lng":9.2102,"city":"Milan","province":"Lombardia","country":"Italia"},
    {"id":"Venice_Day_Trip","type":"activity","start":"2023-10-10 08:45:00","end":"2023-10-10 19:45:00","lat":45.4344,"lng":12.3381,"city":"Venecia","province":"Veneto","country":"Italia"},
    {"id":"Sarajevo_Trip_Base","type":"hotel","start":"2023-04-29 12:00:00","end":"2023-04-30 23:59:00","lat":43.8563,"lng":18.4131,"city":"Sarajevo","province":"Bosnia","country":"Bosnia y Herzegovina"},
    {"id":"Mostar_Trip_Base","type":"hotel","start":"2023-05-01 08:00:00","end":"2023-05-02 23:59:00","lat":43.3438,"lng":17.8078,"city":"Mostar","province":"Herzegovina","country":"Bosnia y Herzegovina"},
    {"id":"Jajce_Trip_Base","type":"hotel","start":"2023-05-03 08:00:00","end":"2023-05-04 15:00:00","lat":44.3419,"lng":17.2703,"city":"Jajce","province":"Bosnia","country":"Bosnia y Herzegovina"},
    {"id":"Bihac_Trip_Base","type":"hotel","start":"2023-05-04 15:00:00","end":"2023-05-06 12:00:00","lat":44.8169,"lng":15.8708,"city":"Bihac","province":"Bosnia","country":"Bosnia y Herzegovina"},
]

def parse_dt(s):
    try: return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except: return None

def match_anchor(photo_dt, anchor):
    a_start = parse_dt(anchor["start"])
    a_end = parse_dt(anchor["end"])
    if not a_start or not a_end: return False
    return a_start <= photo_dt <= a_end

def main():
    mode = "[DRY RUN]" if DRY_RUN else "[EJECUCION REAL]"
    print(f"\n{'='*60}")
    print(f"  {mode} Propagacion de GPS desde Vouchers")
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

    existing = {r[1] for r in c.execute("PRAGMA table_info(photos)").fetchall()}
    for col, typ, default in [
        ("location_source", "TEXT", "'EXIF_GPS'"),
        ("inherited_from_voucher_id", "TEXT", None),
        ("city", "TEXT", None),
        ("province", "TEXT", None),
        ("country", "TEXT", None),
    ]:
        if col not in existing:
            d = f" DEFAULT {default}" if default else ""
            c.execute(f"ALTER TABLE photos ADD COLUMN {col} {typ}{d}")
            print(f"  [OK] Columna {col} agregada")
    conn.commit()

    native_gps = c.execute("SELECT COUNT(*) FROM photos WHERE lat IS NOT NULL AND lat != 0").fetchone()[0]
    no_gps = c.execute("SELECT COUNT(*) FROM photos WHERE lat IS NULL OR lat = 0").fetchone()[0]
    print(f"\n  Fotos con EXIF_GPS nativo: {native_gps}")
    print(f"  Fotos sin GPS (candidatas): {no_gps}")
    print(f"  Anclas: {len(ANCHORS)} ({sum(1 for a in ANCHORS if a['type']=='activity')} act, {sum(1 for a in ANCHORS if a['type']=='hotel')} hot)")

    anchors_sorted = sorted(ANCHORS, key=lambda a: (0 if a["type"] == "activity" else 1))

    rows = c.execute("SELECT id, final_path, year, month_folder FROM photos WHERE lat IS NULL OR lat = 0").fetchall()
    print(f"  Procesando {len(rows)} fotos...")

    stats = {}
    updated = 0
    batch = []

    for i, (pid, fpath, year, mf) in enumerate(rows):
        if i % 5000 == 0 and i > 0:
            print(f"    ...{i}/{len(rows)} ({updated} actualizadas)")

        if not fpath: continue
        fp = Path(fpath)
        if not fp.exists(): continue

        try:
            photo_dt = datetime.fromtimestamp(os.path.getmtime(str(fp)))
        except: continue

        matched = None
        for anchor in anchors_sorted:
            if match_anchor(photo_dt, anchor):
                matched = anchor
                break

        if matched:
            updated += 1
            stats[matched["id"]] = stats.get(matched["id"], 0) + 1
            batch.append((
                matched["lat"], matched["lng"],
                matched["city"], matched["province"], matched["country"],
                "VOUCHER_INHERITANCE", matched["id"], pid
            ))

        if len(batch) >= 1000:
            c.executemany("UPDATE photos SET lat=?, lng=?, city=?, province=?, country=?, location_source=?, inherited_from_voucher_id=? WHERE id=?", batch)
            conn.commit(); batch = []

    if batch:
        c.executemany("UPDATE photos SET lat=?, lng=?, city=?, province=?, country=?, location_source=?, inherited_from_voucher_id=? WHERE id=?", batch)
        conn.commit()

    total_after = c.execute("SELECT COUNT(*) FROM photos WHERE lat IS NOT NULL AND lat != 0").fetchone()[0]
    still_no = c.execute("SELECT COUNT(*) FROM photos WHERE lat IS NULL OR lat = 0").fetchone()[0]
    conn.close()

    print(f"\n{'='*60}")
    print(f"  REPORTE FINAL {'DRY RUN' if DRY_RUN else 'APLICADO'}")
    print(f"{'='*60}")
    print(f"  EXIF_GPS nativo:         {native_gps}")
    print(f"  Heredados de vouchers:   {updated}")
    print(f"  Total con GPS ahora:     {total_after}")
    print(f"  Todavia sin GPS:         {still_no}")
    print(f"\n  --- Detalle por Anchor ---")
    for aid, cnt in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"    {aid}: {cnt} fotos")

    if DRY_RUN:
        print(f"\n  [!] Re-ejecuta sin --dry-run para aplicar")
    else:
        print(f"\n  [OK] Base de datos actualizada")

if __name__ == "__main__":
    main()
