import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- TODOS LOS TRIP_NAMES EN DB ---")
rows = conn.execute("SELECT trip_name, COUNT(*) FROM photos GROUP BY trip_name").fetchall()
for r in rows:
    print(f" - {r['trip_name']}: {r['count(*)']} fotos")

conn.close()
