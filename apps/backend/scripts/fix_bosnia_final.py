import os
import sys
import io
import shutil
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- REUBICANDO FOTOS DE BOSNIA Y ACTUALIZANDO DB ---")

bosnia_src = r"F:\Fotos_Organizadas\Viajes\Bosnia_2023"
target_dir = r"F:\2023\05-Mayo"
os.makedirs(target_dir, exist_ok=True)

rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = 'bosnia-2023'").fetchall()
count = 0

for row in rows:
    pid = row["id"]
    p = row["original_path"].replace("\\\\", "\\")
    if os.path.exists(p):
        f = os.path.basename(p)
        base, ext = os.path.splitext(f)
        tag = "Bosnia_2023"
        
        if tag not in base:
            new_f = f"{base}_{tag}{ext}"
        else:
            new_f = f
            
        new_p = os.path.join(target_dir, new_f)
        if not os.path.exists(new_p):
            shutil.move(p, new_p)
        else:
            os.remove(p)
            
        conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (new_p, new_p, pid))
        count += 1

conn.commit()
conn.close()
print(f"Bosnia 2023: {count} fotos reubicadas a F:\\2023\\05-Mayo y etiquetadas.")
