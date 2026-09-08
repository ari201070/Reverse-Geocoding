import os
import sys
import io
import shutil
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

source_dir = r"F:\.Papelera_Deduplicacion2015\Julio\Slovenia trip"
target_dir = r"F:\2015\07-Julio"
DB_PATH = r"F:\photo_catalog.db"

os.makedirs(target_dir, exist_ok=True)

print(f"--- RESCATANDO FOTOS DE {source_dir} ---")

if os.path.exists(source_dir):
    files = os.listdir(source_dir)
    print(f"Encontrados {len(files)} archivos en Slovenia trip.")
    
    conn = sqlite3.connect(DB_PATH)
    
    moved = 0
    for f in files:
        src = os.path.join(source_dir, f)
        if os.path.isfile(src):
            dest = os.path.join(target_dir, f)
            if os.path.exists(dest):
                os.remove(src)
            else:
                shutil.move(src, dest)
                moved += 1
                
            # Update DB paths if needed
            conn.execute("""
                UPDATE photos 
                SET original_path = ?, final_path = ? 
                WHERE original_path LIKE ? OR final_path LIKE ?
            """, (dest, dest, f"%{f}%", f"%{f}%"))
            
    conn.commit()
    conn.close()
    print(f"Total fotos rescatadas y movidas a F:\\2015\\07-Julio: {moved}")
    
    # Remove source folder
    shutil.rmtree(r"F:\.Papelera_Deduplicacion2015", ignore_errors=True)
else:
    print("La ruta fuente no existe.")
