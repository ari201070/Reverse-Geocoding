import os
import sys
import io
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

print("--- ASEGURANDO ETIQUETADO FÍSICO Y DB PARA TODOS LOS VIAJES ---")

for trip_code, tag in TRIP_TAG_MAPPINGS.items():
    rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = ?", (trip_code,)).fetchall()
    count = 0
    for row in rows:
        pid = row["id"]
        p = os.path.normpath(row["original_path"].replace("\\\\", "\\"))
        
        d = os.path.dirname(p)
        f = os.path.basename(p)
        base, ext = os.path.splitext(f)
        
        # If tag is not in base, add it
        if tag not in base:
            # Check if there is already a version with tag in folder
            tagged_name = f"{base}_{tag}{ext}"
            tagged_path = os.path.join(d, tagged_name)
            
            if os.path.exists(tagged_path):
                # Point DB to already tagged version
                conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (tagged_path, tagged_path, pid))
                count += 1
            elif os.path.exists(p):
                new_p = os.path.join(d, tagged_name)
                os.rename(p, new_p)
                conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (new_p, new_p, pid))
                count += 1
                
    print(f"Viaje {trip_code}: {count} rutas sincronizadas/etiquetadas.")

conn.commit()
conn.close()
print("¡Proceso completado para todos los viajes!")
