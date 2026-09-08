import os
import sys
import io
import shutil
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"

TRIP_TAG_MAPPINGS = {
    "argentina-2011": "Argentina_2011",
    "bosnia-2023": "Bosnia_2023",
    "montenegro-2010": "Croacia_Montenegro_2010",
    "creta-2013": "Creta_2013",
    "italia-2023": "Italia_2023",
    "slovenia-2015": "Eslovenia_2015",
    "argentina-2025": "Argentina_2025",
    "israel-2023": "Israel_2023"
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- EXTRACCIÓN Y LIMPIEZA TOTAL FUERA DE Fotos_Organizadas ---")

for trip_code, tag in TRIP_TAG_MAPPINGS.items():
    rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = ? AND original_path LIKE '%Fotos_Organizadas%'", (trip_code,)).fetchall()
    count = 0
    
    for row in rows:
        pid = row["id"]
        p = row["original_path"].replace("\\\\", "\\")
        if os.path.exists(p):
            f = os.path.basename(p)
            base, ext = os.path.splitext(f)
            
            # Determine year/month from trip or filename
            yyyy = "2023"
            mm = "05-Mayo"
            if "2011" in trip_code: yyyy, mm = "2011", "11-Noviembre"
            elif "2010" in trip_code: yyyy, mm = "2010", "06-Junio"
            elif "2013" in trip_code: yyyy, mm = "2013", "07-Julio"
            elif "2015" in trip_code: yyyy, mm = "2015", "07-Julio"
            elif "2025" in trip_code: yyyy, mm = "2025", "10-Octubre"
            elif "2023" in trip_code and "italia" in trip_code: yyyy, mm = "2023", "10-Octubre"
            
            target_dir = os.path.join(r"F:\\", yyyy, mm)
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
            
    print(f"Viaje {trip_code}: {count} fotos rescatadas de Fotos_Organizadas y ubicadas en su año.")

conn.commit()
conn.close()
print("¡Limpieza de Fotos_Organizadas completada!")
