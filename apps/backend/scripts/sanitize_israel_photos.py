import sqlite3
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"

def get_h3_index(lat, lng):
    try:
        import h3
        return h3.geo_to_h3(lat, lng, 9)
    except Exception:
        return None

def main():
    print("=" * 60)
    print("SANITIZE & REASSIGN ISRAEL PHOTOS")
    print(datetime.now().isoformat())
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure columns exist
    cols = [r[1] for r in conn.execute("PRAGMA table_info(photos)").fetchall()]
    if "confidence_score" not in cols:
        conn.execute("ALTER TABLE photos ADD COLUMN confidence_score REAL")
    if "h3_index" not in cols:
        conn.execute("ALTER TABLE photos ADD COLUMN h3_index TEXT")
    conn.commit()

    # Pre-count report
    print("\n--- REPORT ANTES DE LA REASIGNACIÓN ---")
    bosnia_count = conn.execute("SELECT COUNT(*) FROM photos WHERE trip_name = 'bosnia-2023'").fetchone()[0]
    israel_count = conn.execute("SELECT COUNT(*) FROM photos WHERE trip_name = 'israel-2023'").fetchone()[0]
    print(f"Fotos en trip_name = 'bosnia-2023': {bosnia_count}")
    print(f"Fotos en trip_name = 'israel-2023': {israel_count}")

    # Fetch candidates matching trip_name = 'bosnia-2023' and date_taken between 2023-05-08 and 2023-05-28
    # We retrieve all bosnia-2023 with date_taken and filter in python to robustly handle date formats (hyphens vs colons)
    candidates = conn.execute("""
        SELECT id, date_taken, original_path, final_path FROM photos 
        WHERE trip_name = 'bosnia-2023' AND date_taken IS NOT NULL
    """).fetchall()

    matched_ids = []
    for row in candidates:
        dt_str = row["date_taken"]
        if not dt_str:
            continue
        # Normalize date format YYYY:MM:DD -> YYYY-MM-DD
        normalized_date = dt_str[:10].replace(":", "-")
        if "2023-05-08" <= normalized_date <= "2023-05-28":
            matched_ids.append(row["id"])

    print(f"\nCandidatos detectados para reasignar a Israel (2023-05-08 a 2023-05-28): {len(matched_ids)}")

    if matched_ids:
        lat = 32.0158
        lng = 34.7874
        city = "Holon"
        country = "Israel"
        location_source = "LOCAL_FALLBACK"
        confidence_score = 0.80
        h3_idx = get_h3_index(lat, lng)

        placeholders = ",".join(["?"] * len(matched_ids))
        query = f"""
            UPDATE photos 
            SET trip_name = 'israel-2023',
                lat = ?, 
                lng = ?, 
                city = ?, 
                country = ?, 
                location_source = ?, 
                confidence_score = ?, 
                h3_index = ?
            WHERE id IN ({placeholders})
        """
        params = [lat, lng, city, country, location_source, confidence_score, h3_idx] + matched_ids
        conn.execute(query, params)
        conn.commit()

    # Post-count report
    print("\n--- REPORT DESPUÉS DE LA REASIGNACIÓN ---")
    bosnia_count_post = conn.execute("SELECT COUNT(*) FROM photos WHERE trip_name = 'bosnia-2023'").fetchone()[0]
    israel_count_post = conn.execute("SELECT COUNT(*) FROM photos WHERE trip_name = 'israel-2023'").fetchone()[0]
    print(f"Fotos en trip_name = 'bosnia-2023': {bosnia_count_post}")
    print(f"Fotos en trip_name = 'israel-2023': {israel_count_post} (+{len(matched_ids)})")
    print(f"Registros reasignados con éxito: {len(matched_ids)}")

    conn.close()
    print("=" * 60)

if __name__ == "__main__":
    main()
