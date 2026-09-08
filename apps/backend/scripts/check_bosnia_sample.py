import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

conn = sqlite3.connect(r'F:\photo_catalog.db')
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT trip_name, original_path FROM photos WHERE trip_name = 'bosnia-2023' LIMIT 1").fetchone()
print(f"Viaje: {row['trip_name']} -> Ruta: {row['original_path']}")
conn.close()
