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

print("--- RESCATANDO Y ETIQUETANDO FOTOS DE BOSNIA ---")

rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = 'bosnia-2023'").fetchall()
count = 0
for row in rows:
    pid = row["id"]
    p = row["original_path"].replace("\\\\", "\\")
    
    # If path points to Fotos_Organizadas, find actual file in F:\2023\05-Mayo
    if "Fotos_Organizadas" in p:
        fname = os.path.basename(p)
        base, ext = os.path.splitext(fname)
        tag = "Bosnia_2023"
        if tag not in base:
            new_f = f"{base}_{tag}{ext}"
        else:
            new_f = fname
            
        target_path = os.path.join(r"F:\2023\05-Mayo", new_f)
        if os.path.exists(target_path):
            conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (target_path, target_path, pid))
            count += 1

conn.commit()
conn.close()
print(f"Registros de Bosnia actualizados con ruta etiquetada en F:\\2023\\05-Mayo: {count}")
