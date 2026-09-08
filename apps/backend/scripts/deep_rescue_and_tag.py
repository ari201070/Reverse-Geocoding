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

print("--- RESCATE Y ACTUALIZACIÓN PROFUNDA DESDE FOTOS_ORGANIZADAS ---")

for trip_code, info in TRIP_TAG_MAPPINGS.items():
    tag, def_yyyy, def_mm = info
    rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = ?", (trip_code,)).fetchall()
    
    rescued = 0
    for row in rows:
        pid = row["id"]
        p = row["original_path"].replace("\\\\", "\\")
        
        # If file doesn't exist at stored path, search by filename in F:\
        if not os.path.exists(p):
            fname = os.path.basename(p)
            # Search in F:\2011, F:\2013, F:\2023, etc.
            found_path = None
            for root, dirs, files in os.walk(r"F:\\"):
                if "Fotos_Organizadas" in root or ".Papelera" in root:
                    continue
                if fname in files:
                    found_path = os.path.join(root, fname)
                    break
            if found_path:
                p = found_path
                
        if os.path.exists(p):
            d = os.path.dirname(p)
            f = os.path.basename(p)
            base, ext = os.path.splitext(f)
            
            if tag not in base:
                new_f = f"{base}_{tag}{ext}"
                new_p = os.path.join(d, new_f)
                if not os.path.exists(new_p):
                    os.rename(p, new_p)
                else:
                    new_p = p
                p = new_p
                
            conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (p, p, pid))
            rescued += 1
            
    print(f"Viaje {trip_code}: {rescued} fotos localizadas, etiquetadas y sincronizadas.")

conn.commit()
conn.close()
print("¡Sincronización profunda completada!")
