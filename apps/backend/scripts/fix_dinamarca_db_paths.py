import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)

# Fix path prefix in DB from F:\2024\Septiembre to F:\2024\09-Septiembre
conn.execute("""
    UPDATE photos 
    SET original_path = REPLACE(original_path, 'F:\\2024\\Septiembre\\', 'F:\\2024\\09-Septiembre\\'),
        final_path = REPLACE(final_path, 'F:\\2024\\Septiembre\\', 'F:\\2024\\09-Septiembre\\')
    WHERE trip_name = 'dinamarca-2024'
""")
conn.commit()
conn.close()
print("Rutas de Dinamarca corregidas en DB.")
