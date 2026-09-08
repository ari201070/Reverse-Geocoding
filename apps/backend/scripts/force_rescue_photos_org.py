import os
import sys
import io
import shutil
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
TRIP_TAG_MAPPINGS = {
    "argentina-2011": ("Argentina_2011", "2011", "11-Noviembre"),
    "bosnia-2023": ("Bosnia_2023", "2023", "05-Mayo"),
    "montenegro-2010": ("Croacia_Montenegro_2010", "2010", "06-Junio"),
    "creta-2013": ("Creta_2013", "2013", "07-Julio"),
    "italia-2023": ("Italia_2023", "2023", "10-Octubre"),
    "slovenia-2015": ("Eslovenia_2015", "2015", "07-Julio"),
    "argentina-2025": ("Argentina_2025", "2025", "10-Octubre"),
    "israel-2023": ("Israel_2023", "2023", "05-Mayo")
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- FORZANDO RESCATE REAL DE FOTOS DESDE Fotos_Organizadas ---")

for trip_code, info in TRIP_TAG_MAPPINGS.items():
    tag, def_yyyy, def_mm = info
    rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = ? AND original_path LIKE '%Fotos_Organizadas%'", (trip_code,)).fetchall()
    
    count = 0
    for row in rows:
        pid = row["id"]
        p = row["original_path"].replace("\\\\", "\\")
        if os.path.exists(p):
            f = os.path.basename(p)
            base, ext = os.path.splitext(f)
            
            target_dir = os.path.join(r"F:\\", def_yyyy, def_mm)
            os.makedirs(target_dir, exist_ok=True)
            
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
            
    print(f"Viaje {trip_code}: {count} fotos rescatadas físicamente y actualizadas en DB.")

conn.commit()
conn.close()
print("¡Rescate finalizado con éxito!")
