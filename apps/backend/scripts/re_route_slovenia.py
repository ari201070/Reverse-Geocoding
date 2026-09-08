import os
import sys
import io
import shutil
import sqlite3
import hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"
DB_PATH = r"F:\photo_catalog.db"

print("--- REUBICANDO Y ACTUALIZANDO FOTOS DE ESLOVENIA 2015 ---")

target_slovenia_dir = os.path.join(root_drive, "2015", "07-Julio")
os.makedirs(target_slovenia_dir, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, original_path, final_path FROM photos WHERE trip_name = 'slovenia-2015'").fetchall()

moved_count = 0
for r in rows:
    path = r["original_path"] or r["final_path"]
    if path and os.path.exists(path):
        fname = os.path.basename(path)
        dest = os.path.join(target_slovenia_dir, fname)
        if os.path.abspath(path) != os.path.abspath(dest):
            if os.path.exists(dest):
                os.remove(path)
            else:
                shutil.move(path, dest)
            
            # Update DB path
            conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (dest, dest, r["id"]))
            moved_count += 1

conn.commit()
conn.close()

print(f"Total fotos de Eslovenia reubicadas a F:\\2015\\07-Julio y actualizadas en DB: {moved_count}")
