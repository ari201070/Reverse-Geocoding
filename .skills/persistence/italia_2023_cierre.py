#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys, io, sqlite3, h3
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

# Anchors for the last 2 days (Oct 11-12)
SOPGA = {"lat":45.4885,"lng":9.2102,"city":"Milan","province":"Lombardia","country":"Italia","id":"Hotel_Soperga_Milan"}
MALPENSA = {"lat":45.6300,"lng":8.7250,"city":"Varese","province":"Lombardia","country":"Italia","id":"Milan_Malpensa_MXP"}

# Cutoffs
TRIP_END = datetime(2023, 10, 12, 23, 59, 59)
DOMESTIC_START = datetime(2023, 10, 13, 0, 0, 0)
ELIGIBLE_START = datetime(2023, 10, 11, 0, 0, 0)
MALPENSA_WINDOW = datetime(2023, 10, 12, 10, 30, 0)

def parse_dt(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H.%M.%S", "%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H.%M.%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def main():
    sep = "=" * 60
    print(f"\n{sep}")
    print("  Italia 2023 - Cierre: Anclas 11-12 Octubre")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(sep)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    c = conn.cursor()

    # Get all Oct 2023 photos without GPS, eligible window only
    photos = c.execute("""
        SELECT id, filename, date_taken, lat
        FROM photos
        WHERE year = 2023 AND month_folder = '10-Octubre'
          AND (lat IS NULL OR lat = 0)
        ORDER BY date_taken ASC
    """).fetchall()

    print(f"\n  [FASE 1] Analisis de {len(photos)} fotos sin GPS en Oct 2023")

    eligible = []
    skipped_domestic = 0
    skipped_no_date = 0
    skipped_outside = 0

    for pid, fname, dt_str, current_lat in photos:
        if current_lat is not None and current_lat != 0:
            skipped_outside += 1
            continue
        if not dt_str:
            skipped_no_date += 1
            continue
        photo_dt = parse_dt(dt_str)
        if not photo_dt:
            skipped_no_date += 1
            continue

        if photo_dt >= DOMESTIC_START:
            skipped_domestic += 1
            continue
        if photo_dt < ELIGIBLE_START:
            skipped_outside += 1
            continue

        eligible.append((pid, fname, photo_dt))

    print(f"    Elegibles (11-12 Oct):    {len(eligible)}")
    print(f"    Fuera de rango:           {skipped_outside}")
    print(f"    Sin fecha parseable:      {skipped_no_date}")
    print(f"    Domesticas (>= 13 Oct):   {skipped_domestic}")

    # Classify eligible
    print(f"\n  [FASE 2] Clasificacion por horario 12 Octubre...")
    batch = []
    count_soperga = 0
    count_malpensa = 0
    count_unknown = 0

    for pid, fname, photo_dt in eligible:
        anchor = None
        if photo_dt.day == 12 and photo_dt.hour == 12 and photo_dt.minute < 30:
            # Oct 12 before 10:30 -> Soperga
            anchor = SOPGA
            count_soperga += 1
        elif photo_dt.day == 12 and photo_dt.hour == 12 and photo_dt.minute >= 30:
            # Oct 12 10:30-12:59 -> Malpensa
            anchor = MALPENSA
            count_malpensa += 1
        elif photo_dt.day == 12 and photo_dt.hour in (10,11):
            if photo_dt.hour == 10 and photo_dt.minute < 30:
                anchor = SOPGA
                count_soperga += 1
            else:
                anchor = MALPENSA
                count_malpensa += 1
        elif photo_dt.day == 12 and photo_dt.hour >= 13:
            # After 1PM -> flight, skip
            count_unknown += 1
            continue
        elif photo_dt.day == 11:
            # Oct 11 -> still in Milan (Soperga)
            anchor = SOPGA
            count_soperga += 1
        else:
            count_unknown += 1
            continue

        if anchor:
            h3_cell = h3.latlng_to_cell(round(anchor["lat"], 6), round(anchor["lng"], 6), 9)
            batch.append((
                anchor["lat"], anchor["lng"],
                anchor["city"], anchor["province"], anchor["country"],
                "VOUCHER_INHERITANCE", anchor["id"], h3_cell, pid
            ))

    print(f"    Soperga (Milan):          {count_soperga}")
    print(f"    Malpensa (MXP):           {count_malpensa}")
    print(f"    Vuelo/post-aterrizaje:    {count_unknown} (no modificadas)")

    # Write DB
    print(f"\n  [FASE 3] Escritura en DB...")
    if batch:
        c.executemany("""
            UPDATE photos SET lat=?, lng=?, city=?, province=?, country=?,
                location_source=?, inherited_from_voucher_id=?, h3_index=?
            WHERE id=?
        """, batch)
        conn.commit()
        print(f"    Registros actualizados:   {len(batch)}")
    else:
        print("    Sin registros para actualizar")

    # Final report
    total = c.execute("SELECT COUNT(*) FROM photos WHERE year=2023 AND month_folder='10-Octubre'").fetchone()[0]
    with_gps = c.execute("SELECT COUNT(*) FROM photos WHERE year=2023 AND month_folder='10-Octubre' AND lat IS NOT NULL AND lat != 0").fetchone()[0]
    voucher_total = c.execute("SELECT COUNT(*) FROM photos WHERE year=2023 AND month_folder='10-Octubre' AND location_source='VOUCHER_INHERITANCE'").fetchone()[0]
    still_no_gps = c.execute("SELECT COUNT(*) FROM photos WHERE year=2023 AND month_folder='10-Octubre' AND (lat IS NULL OR lat=0)").fetchone()[0]
    conn.close()

    print(f"\n{sep}")
    print("  RESUMEN FINAL ITALIA 2023")
    print(sep)
    print(f"  Total fotos Oct 2023:        {total}")
    print(f"  Con GPS total ahora:         {with_gps} ({with_gps*100//total}%)")
    print(f"  VOUCHER_INHERITANCE total:   {voucher_total}")
    print(f"  Cierre 11-12 Oct +{len(batch)}:     Soperga={count_soperga} | Malpensa={count_malpensa}")
    print(f"  Restan sin GPS:              {still_no_gps}")
    print(sep)

if __name__ == "__main__":
    main()
