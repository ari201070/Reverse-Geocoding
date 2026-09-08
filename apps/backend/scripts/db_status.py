import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- ESTADO ACTUAL DE LA BASE DE DATOS ---")
rows = conn.execute("SELECT trip_name, COUNT(*) FROM photos GROUP BY trip_name").fetchall()
for r in rows:
    print(f" - {r[0]}: {r[1]} fotos")

total = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
print(f"Total registros en DB: {total}")
conn.close()
