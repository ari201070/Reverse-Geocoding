import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- BUSCANDO FOTOS EN DB CON RUTA QUE CONTENGA 2024 ---")
rows = conn.execute("SELECT id, trip_name, original_path FROM photos WHERE original_path LIKE '%2024%' LIMIT 15").fetchall()
for r in rows:
    print(r["id"], r["trip_name"], r["original_path"])

conn.close()
