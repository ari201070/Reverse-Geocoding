import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

conn = sqlite3.connect(r'F:\photo_catalog.db')
conn.row_factory = sqlite3.Row

trips = [
    "argentina-2011",
    "bosnia-2023",
    "montenegro-2010",
    "creta-2013",
    "italia-2023",
    "slovenia-2015",
    "argentina-2025",
    "israel-2023"
]

print("--- EJEMPLOS POR CADA VIAJE EN LA DB ---")
for t in trips:
    row = conn.execute("SELECT trip_name, original_path FROM photos WHERE trip_name = ? LIMIT 1", (t,)).fetchone()
    if row:
        print(f"Viaje: {row['trip_name']} -> Ruta: {row['original_path']}")
    else:
        print(f"Viaje: {t} -> Sin registros")

conn.close()
