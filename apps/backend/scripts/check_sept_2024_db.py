import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- REGISTROS EN DB PARA SEPTIEMBRE 2024 ---")
rows = conn.execute("SELECT id, trip_name, original_path FROM photos WHERE original_path LIKE '%2024\\09-Septiembre%' OR original_path LIKE '%2024/09-Septiembre%' LIMIT 10").fetchall()
for r in rows:
    print(r["trip_name"], r["original_path"])

conn.close()
