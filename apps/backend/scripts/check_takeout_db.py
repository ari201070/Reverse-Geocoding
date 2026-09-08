import sqlite3
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
takeout_folder = r"F:\copia de los datos de Google\Takeout"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

count = conn.execute("SELECT COUNT(*) FROM photos WHERE original_path LIKE ? OR final_path LIKE ?", (f"%{takeout_folder}%", f"%{takeout_folder}%")).fetchone()[0]
print(f"Fotos en DB que apuntan a Takeout: {count}")

conn.close()
