import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- ACTUALIZANDO BASE DE DATOS PARA ESLOVENIA 2015 ---")

# Let's update trip_name for photos in F:\2015\07-Julio that belong to Eslovenia
updated = conn.execute("""
    UPDATE photos 
    SET trip_name = 'slovenia-2015', 
        country = 'Eslovenia', 
        location_source = 'LOCAL_FALLBACK', 
        confidence_score = 0.90
    WHERE (original_path LIKE '%2015/07-Julio%' OR original_path LIKE '%2015\\07-Julio%')
      AND (lat IS NULL OR lat = 0)
""")
conn.commit()
print(f"Registros actualizados a 'slovenia-2015': {updated.rowcount}")

# Check total slovenia-2015 count now
total_slov = conn.execute("SELECT COUNT(*) FROM photos WHERE trip_name = 'slovenia-2015'").fetchone()[0]
print(f"Total fotos en 'slovenia-2015': {total_slov}")

conn.close()
