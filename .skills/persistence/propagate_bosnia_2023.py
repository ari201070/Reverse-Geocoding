# -*- coding: utf-8 -*-
import os
import sys, io, sqlite3, h3
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

TRIP_START = datetime(2023, 4, 29)
TRIP_END = datetime(2023, 5, 6, 23, 59, 59)

ANCHORS = {
    29: {"lat":43.8200,"lng":18.3475,"city":"Sarajevo","province":"Federacija BiH","country":"Bosnia y Herzegovina","desc":"Tunel de la Esperanza"},
    30: {"lat":43.8563,"lng":18.4131,"city":"Sarajevo","province":"Federacija BiH","country":"Bosnia y Herzegovina","desc":"Sarajevo Centro"},
    # May 1: morning Konjic, afternoon Mostar
    1:  {"lat":43.3373,"lng":17.8150,"city":"Mostar","province":"Federacija BiH","country":"Bosnia y Herzegovina","desc":"Stari Most"},
    2:  {"lat":43.1585,"lng":17.6083,"city":"Stolac","province":"Federacija BiH","country":"Bosnia y Herzegovina","desc":"Kravice Falls"},
    3:  {"lat":44.3421,"lng":17.2701,"city":"Jajce","province":"Federacija BiH","country":"Bosnia y Herzegovina","desc":"Jajce Centro"},
    4:  {"lat":44.3444,"lng":17.2251,"city":"Jajce","province":"Federacija BiH","country":"Bosnia y Herzegovina","desc":"Pliva Lakes"},
    5:  {"lat":44.6558,"lng":16.0125,"city":"Bihac","province":"Federacija BiH","country":"Bosnia y Herzegovina","desc":"Una NP"},
    6:  {"lat":45.8150,"lng":15.9819,"city":"Zagreb","province":"Zagreb","country":"Croacia","desc":"Zagreb Centro"},
}

# Konjic anchor for May 1 morning
KONJIC = {"lat":43.6338,"lng":17.9942,"city":"Konjic","province":"Federacija BiH","country":"Bosnia y Herzegovina","desc":"Bunker Tito"}

def parse_dt(s):
    if not s: return None
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H.%M.%S","%Y:%m:%d %H:%M:%S","%Y:%m:%d %H.%M.%S"):
        try: return datetime.strptime(s, fmt)
        except: pass
    return None

def get_anchor(photo_dt):
    day = photo_dt.day
    month = photo_dt.month
    if month == 4 and day == 29:
        return ANCHORS[29]
    elif month == 4 and day == 30:
        return ANCHORS[30]
    elif month == 5 and day == 1:
        # Morning -> Konjic, afternoon -> Mostar
        if photo_dt.hour < 13:
            return KONJIC
        return ANCHORS[1]
    elif month == 5 and day in ANCHORS:
        return ANCHORS[day]
    return None

def main():
    sep = "=" * 60
    print()
    print(sep)
    print("  BOSNIA 2023 - Propagacion de Anclas")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(sep)

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    c = conn.cursor()

    # Add trip_name column if not exists
    try: c.execute("ALTER TABLE photos ADD COLUMN trip_name TEXT")
    except: pass
    conn.commit()

    photos = c.execute("""
        SELECT id, filename, final_path, date_taken, lat, lng, trip_name
        FROM photos
        WHERE date_taken BETWEEN "2023-04-29" AND "2023-05-06 23:59:59"
        ORDER BY date_taken ASC
    """).fetchall()

    print()
    print("  Fotos en rango 29 Apr - 6 May 2023: " + str(len(photos)))

    stats = {"tagged":0, "geolocated":0, "already_gps":0, "no_date":0, "skipped":0}
    batch = []

    for pid, fname, fpath, dt_str, lat, lng, existing_trip in photos:
        if not dt_str:
            stats["no_date"] += 1
            continue

        photo_dt = parse_dt(dt_str)
        if not photo_dt or not (TRIP_START <= photo_dt <= TRIP_END):
            stats["skipped"] += 1
            continue

        # Tag trip_name
        if existing_trip != "bosnia-2023":
            stats["tagged"] += 1

        # Get anchor
        anchor = get_anchor(photo_dt)
        if not anchor:
            stats["skipped"] += 1
            continue

        has_gps = lat is not None and lat != 0
        new_lat = anchor["lat"]
        new_lng = anchor["lng"]

        if not has_gps:
            stats["geolocated"] += 1
        else:
            stats["already_gps"] += 1

        h3_cell = h3.latlng_to_cell(round(new_lat, 6), round(new_lng, 6), 9)

        batch.append((
            "bosnia-2023",
            new_lat, new_lng,
            anchor["city"], anchor["province"], anchor["country"],
            "VOUCHER_INHERITANCE", anchor["desc"], h3_cell,
            pid
        ))

    # Execute updates
    if batch:
        c.executemany("""
            UPDATE photos SET
                trip_name=?, lat=?, lng=?, city=?, province=?, country=?,
                location_source=?, location_name=?, h3_index=?
            WHERE id=?
        """, batch)
        conn.commit()

    conn.close()

    print()
    print("  --- RESULTADO ---")
    print("  Trip name asignado:       " + str(stats["tagged"]))
    print("  Fotos georreferenciadas:  " + str(stats["geolocated"]))
    print("  Ya tenian GPS:            " + str(stats["already_gps"]))
    print("  Sin fecha util:           " + str(stats["no_date"]))
    print("  Fuera de rango:           " + str(stats["skipped"]))
    print("  Total procesadas:         " + str(len(batch)))

    # Distribution by day
    print()
    print("  --- Por Dia ---")
    conn2 = sqlite3.connect(DB)
    cursor = conn2.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    for r in conn2.execute("""
        SELECT SUBSTR(date_taken, 1, 10), COUNT(*)
        FROM photos WHERE trip_name="bosnia-2023"
        GROUP BY SUBSTR(date_taken, 1, 10) ORDER BY 1
    """):
        print("    " + r[0] + ": " + str(r[1]) + " fotos")
    conn2.close()

    print()
    print(sep)
    print("  [OK] Bosnia 2023 georreferenciada")
    print(sep)

if __name__ == "__main__":
    main()
