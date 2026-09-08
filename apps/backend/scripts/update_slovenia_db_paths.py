import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
root_drive = r"F:\\"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- ACTUALIZANDO RUTAS EN DB PARA ESLOVENIA 2015 ---")

rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = 'slovenia-2015'").fetchall()

updated = 0
for r in rows:
    old_path = r["original_path"]
    if old_path:
        fname = os.path.basename(old_path)
        new_path = os.path.join(root_drive, "2015", "07-Julio", fname)
        if os.path.exists(new_path):
            conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (new_path, new_path, r["id"]))
            updated += 1

conn.commit()
conn.close()

print(f"Total registros actualizados con su ruta real en F:\\2015\\07-Julio: {updated}")
