import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"

# Mapping of trip codes in DB to their respective tag suffix
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

print("--- APLICANDO ETIQUETADO ESTÁNDAR A TODOS LOS VIAJES ---")

total_tagged = 0

for trip_code, tag in TRIP_TAG_MAPPINGS.items():
    rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = ?", (trip_code,)).fetchall()
    trip_tagged = 0
    
    for row in rows:
        pid = row["id"]
        p = row["original_path"].replace("\\\\", "\\")
        p = os.path.normpath(p)
        
        if os.path.exists(p):
            d, f = os.path.dirname(p), os.path.basename(p)
            base, ext = os.path.splitext(f)
            
            # Check if tag is already present in filename
            if tag not in base:
                new_f = f"{base}_{tag}{ext}"
                new_p = os.path.join(d, new_f)
                
                # If target already exists, avoid overwrite
                if not os.path.exists(new_p):
                    os.rename(p, new_p)
                else:
                    new_p = p # keep original if tagged version exists
                    
                conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (new_p, new_p, pid))
                trip_tagged += 1
                
    print(f"Viaje {trip_code} (Tag: {tag}): {trip_tagged} archivos etiquetados.")
    total_tagged += trip_tagged

conn.commit()
conn.close()

print(f"\n¡Etiquetado estándar completado para todos los viajes! Total archivos actualizados: {total_tagged}")
