import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "photo_catalog.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT id, filename, file_path, date_taken, latitude, longitude, location_name, trip_name
    FROM photos
    WHERE date_taken >= '2023-10-03 09:40:00' AND date_taken <= '2023-10-03 10:20:00'
    ORDER BY date_taken
""")

rows = cursor.fetchall()
print(f"Found {len(rows)} photos between 09:40 and 10:20 on 2023-10-03:")
for r in rows:
    print(f"ID: {r['id']} | File: {r['filename']} | Path: {r['file_path']} | Time: {r['date_taken']} | Coords: {r['latitude']}, {r['longitude']} | Location: {r['location_name']}")

conn.close()