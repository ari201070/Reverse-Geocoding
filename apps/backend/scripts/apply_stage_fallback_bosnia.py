import sqlite3
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"

# Itinerary matrix mapping dates to location data
ITINERARY_MATRIX = {
    "2023-04-29": {"lat": 43.8563, "lng": 18.4131, "city": "Sarajevo", "country": "Bosnia"},
    "2023-04-30": {"lat": 43.8563, "lng": 18.4131, "city": "Sarajevo", "country": "Bosnia"},
    "2023-05-01": {"lat": 43.3438, "lng": 17.8078, "city": "Mostar", "country": "Bosnia"},
    "2023-05-02": {"lat": 43.3438, "lng": 17.8078, "city": "Mostar", "country": "Bosnia"},
    "2023-05-03": {"lat": 44.3417, "lng": 17.2681, "city": "Jajce", "country": "Bosnia"},
    "2023-05-04": {"lat": 44.8167, "lng": 15.8708, "city": "Bihac", "country": "Bosnia"},
    "2023-05-05": {"lat": 44.8167, "lng": 15.8708, "city": "Bihac", "country": "Bosnia"},
    "2023-05-06": {"lat": 45.8150, "lng": 15.9819, "city": "Zagreb", "country": "Croacia"},
}

def get_h3_index(lat, lng):
    try:
        import h3
        return h3.geo_to_h3(lat, lng, 9)
    except Exception:
        return None

def main():
    print("=" * 60)
    print("STAGE FALLBACK INJECTOR FOR BOSNIA")
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
    print("\n--- REPORT ANTES DE LA INYECCIÓN ---")
    total_bosnia = conn.execute("""
        SELECT COUNT(*) FROM photos 
        WHERE trip_name = 'bosnia-2023' OR original_path LIKE '%Bosnia%' OR final_path LIKE '%Bosnia%'
    """).fetchone()[0]

    unmapped_bosnia_with_date = conn.execute("""
        SELECT COUNT(*) FROM photos 
        WHERE (trip_name = 'bosnia-2023' OR original_path LIKE '%Bosnia%' OR final_path LIKE '%Bosnia%')
          AND date_taken IS NOT NULL 
          AND (lat IS NULL OR lng IS NULL)
    """).fetchone()[0]

    mapped_bosnia = conn.execute("""
        SELECT COUNT(*) FROM photos 
        WHERE (trip_name = 'bosnia-2023' OR original_path LIKE '%Bosnia%' OR final_path LIKE '%Bosnia%')
          AND lat IS NOT NULL AND lng IS NOT NULL
    """).fetchone()[0]

    print(f"Total fotos Bosnia en DB: {total_bosnia}")
    print(f"Fotos Bosnia mapeadas (con lat/lng): {mapped_bosnia}")
    print(f"Fotos Bosnia sin mapear (con fecha, sin lat/lng): {unmapped_bosnia_with_date}")

    # Fetch candidates
    candidates = conn.execute("""
        SELECT id, date_taken, original_path, final_path FROM photos 
        WHERE (trip_name = 'bosnia-2023' OR original_path LIKE '%Bosnia%' OR final_path LIKE '%Bosnia%')
          AND date_taken IS NOT NULL 
          AND (lat IS NULL OR lng IS NULL)
    """).fetchall()

    print(f"\nCandidatos obtenidos para aplicar Stage Fallback: {len(candidates)}")

    updated_count = 0
    skipped_count = 0

    for row in candidates:
        photo_id = row["id"]
        dt_str = row["date_taken"]
        if not dt_str:
            skipped_count += 1
            continue

        # Extract YYYY-MM-DD (handling both hyphens and colons in date separator)
        date_part = dt_str[:10].replace(":", "-")
        if date_part in ITINERARY_MATRIX:
            loc = ITINERARY_MATRIX[date_part]
            h3_idx = get_h3_index(loc["lat"], loc["lng"])

            conn.execute("""
                UPDATE photos 
                SET lat = ?, lng = ?, city = ?, country = ?, 
                    location_source = 'STAGE_FALLBACK', 
                    confidence_score = 0.80, 
                    h3_index = ?
                WHERE id = ?
            """, (loc["lat"], loc["lng"], loc["city"], loc["country"], h3_idx, photo_id))
            updated_count += 1
        else:
            skipped_count += 1

    conn.commit()

    # Post-count report
    print("\n--- REPORT DESPUÉS DE LA INYECCIÓN ---")
    total_bosnia_post = conn.execute("""
        SELECT COUNT(*) FROM photos 
        WHERE trip_name = 'bosnia-2023' OR original_path LIKE '%Bosnia%' OR final_path LIKE '%Bosnia%'
    """).fetchone()[0]

    unmapped_bosnia_with_date_post = conn.execute("""
        SELECT COUNT(*) FROM photos 
        WHERE (trip_name = 'bosnia-2023' OR original_path LIKE '%Bosnia%' OR final_path LIKE '%Bosnia%')
          AND date_taken IS NOT NULL 
          AND (lat IS NULL OR lng IS NULL)
    """).fetchone()[0]

    mapped_bosnia_post = conn.execute("""
        SELECT COUNT(*) FROM photos 
        WHERE (trip_name = 'bosnia-2023' OR original_path LIKE '%Bosnia%' OR final_path LIKE '%Bosnia%')
          AND lat IS NOT NULL AND lng IS NOT NULL
    """).fetchone()[0]

    print(f"Total fotos Bosnia en DB: {total_bosnia_post}")
    print(f"Fotos Bosnia mapeadas (con lat/lng): {mapped_bosnia_post} (+{updated_count})")
    print(f"Fotos Bosnia sin mapear (con fecha, sin lat/lng): {unmapped_bosnia_with_date_post}")
    print(f"Registros actualizados con éxito: {updated_count}")
    print(f"Registros omitidos (fuera de rango de fecha): {skipped_count}")

    conn.close()
    print("=" * 60)

if __name__ == "__main__":
    main()
