#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys, io, sqlite3, h3
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

ANCHORS = [
    {"id":"Sun_Moon_Roma","type":"hotel","start":"2023-10-01 15:59:00","end":"2023-10-05 09:59:00","lat":41.9023,"lng":12.5054,"city":"Roma","province":"Lazio","country":"Italia"},
    {"id":"Museo_Leonardo_da_Vinci_Rome","type":"activity","start":"2023-10-02 17:00:00","end":"2023-10-02 18:59:00","lat":41.8967,"lng":12.4716,"city":"Roma","province":"Lazio","country":"Italia"},
    {"id":"Capilla_Sixtina_Vaticano","type":"activity","start":"2023-10-03 14:30:00","end":"2023-10-03 18:00:00","lat":41.9069,"lng":12.4533,"city":"Ciudad del Vaticano","province":"Vaticano","country":"Vaticano"},
    {"id":"Pantheon_Rome","type":"activity","start":"2023-10-04 11:30:00","end":"2023-10-04 13:00:00","lat":41.8986,"lng":12.4769,"city":"Roma","province":"Lazio","country":"Italia"},
    {"id":"Colosseum_Forum_Tour","type":"activity","start":"2023-10-04 14:30:00","end":"2023-10-04 18:00:00","lat":41.8906,"lng":12.4906,"city":"Roma","province":"Lazio","country":"Italia"},
    {"id":"BB_Marbo_Florence","type":"hotel","start":"2023-10-05 12:59:00","end":"2023-10-06 12:01:00","lat":43.7781,"lng":11.2454,"city":"Florencia","province":"Toscana","country":"Italia"},
    {"id":"Pisa_Day_Trip","type":"activity","start":"2023-10-06 10:05:00","end":"2023-10-06 12:00:00","lat":43.7228,"lng":10.3948,"city":"Pisa","province":"Toscana","country":"Italia"},
    {"id":"Hotel_Soperga_Milan","type":"hotel","start":"2023-10-09 13:59:00","end":"2023-10-12 09:59:00","lat":45.4885,"lng":9.2102,"city":"Milan","province":"Lombardia","country":"Italia"},
    {"id":"Venice_Day_Trip","type":"activity","start":"2023-10-10 08:45:00","end":"2023-10-10 19:45:00","lat":45.4344,"lng":12.3381,"city":"Venecia","province":"Veneto","country":"Italia"},
]

def parse_dt(s):
    try: return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except: return None

def main():
    sep = "=" * 60
    print(f"\n{sep}")
    print("  Italia 2023 - Propagacion TripIt")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(sep)

    anchors = sorted(ANCHORS, key=lambda x: (0 if x["type"] == "activity" else 1))

    # Verify anchors
    print(f"\n  [FASE 1] {len(anchors)} anclas verificadas:")
    for a in anchors:
        tag = "ACT" if a["type"] == "activity" else "HOT"
        print(f"    [{tag}] {a['id']}: ({a['lat']}, {a['lng']})")

    # Load photos
    print("\n  [FASE 2] Cruce con fotos Oct 2023...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    c = conn.cursor()

    photos = c.execute("""
        SELECT id, filename, date_taken, lat
        FROM photos
        WHERE year = 2023 AND month_folder = '10-Octubre'
        ORDER BY date_taken ASC
    """).fetchall()
    print(f"    Total fotos: {len(photos)}")

    no_gps = [p for p in photos if p[3] is None or p[3] == 0]
    print(f"    Sin GPS (candidatas): {len(no_gps)}")

    # Match
    updated = 0
    batch = []
    matches_by_anchor = {}

    for pid, fname, dt_str, current_lat in no_gps:
        if not dt_str:
            continue
        photo_dt = parse_dt(dt_str)
        if not photo_dt:
            continue

        for anchor in anchors:
            a_start = parse_dt(anchor["start"])
            a_end = parse_dt(anchor["end"])
            if a_start and a_end and a_start <= photo_dt <= a_end:
                key = anchor["id"]
                matches_by_anchor[key] = matches_by_anchor.get(key, 0) + 1
                h3_cell = h3.latlng_to_cell(round(anchor["lat"], 6), round(anchor["lng"], 6), 9)
                batch.append((
                    anchor["lat"], anchor["lng"],
                    anchor["city"], anchor["province"], anchor["country"],
                    "VOUCHER_INHERITANCE", anchor["id"], h3_cell, pid
                ))
                updated += 1
                break

    # Write DB
    if batch:
        c.executemany("""
            UPDATE photos SET lat=?, lng=?, city=?, province=?, country=?,
                location_source=?, inherited_from_voucher_id=?, h3_index=?
            WHERE id=?
        """, batch)
        conn.commit()

    # Report
    total_italy = c.execute("SELECT COUNT(*) FROM photos WHERE year=2023 AND month_folder='10-Octubre'").fetchone()[0]
    with_gps = c.execute("SELECT COUNT(*) FROM photos WHERE year=2023 AND month_folder='10-Octubre' AND lat IS NOT NULL AND lat != 0").fetchone()[0]
    voucher = c.execute("SELECT COUNT(*) FROM photos WHERE year=2023 AND month_folder='10-Octubre' AND location_source='VOUCHER_INHERITANCE'").fetchone()[0]
    already_gps = len(photos) - len(no_gps)
    conn.close()

    print(f"\n  [FASE 3] Reporte:")
    print(f"\n{sep}")
    print("  RESUMEN ITALIA 2023")
    print(sep)
    print(f"  Total fotos Oct 2023:        {total_italy}")
    print(f"  Con GPS pre-existente:       {already_gps}")
    print(f"  Heredadas ahora:             {updated}")
    print(f"  Con GPS total ahora:         {with_gps}")
    print(f"  VOUCHER_INHERITANCE total:   {voucher}")
    print(f"\n  --- Detalle por Anchor ---")
    for aid, cnt in sorted(matches_by_anchor.items(), key=lambda x: -x[1]):
        print(f"    {aid}: {cnt} fotos")
    print(f"\n{sep}")
    print(f"  [OK] Italia 2023 georreferenciada")
    print(sep)

if __name__ == "__main__":
    main()
