import os
import sys
import io
import sqlite3
import shutil

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

print("--- FORZANDO ETIQUETADO Y REUBICACIÓN FÍSICA PARA TODOS LOS VIAJES ---")

for trip_code, tag in TRIP_TAG_MAPPINGS.items():
    rows = conn.execute("SELECT id, original_path, final_path FROM photos WHERE trip_name = ?", (trip_code,)).fetchall()
    tagged_count = 0
    
    for row in rows:
        pid = row["id"]
        p = (row["original_path"] or row["final_path"]).replace("\\\\", "\\")
        p = os.path.normpath(p)
        
        # If file is trapped inside old 'Fotos_Organizadas\Viajes', let's move it to its correct year/month folder first
        if "Fotos_Organizadas" in p:
            # Extract filename and try guess year/month from path or name
            f = os.path.basename(p)
            # Default to 2023 or year from trip name if present
            yyyy = "2023"
            if "2011" in trip_code: yyyy = "2011"
            elif "2010" in trip_code: yyyy = "2010"
            elif "2013" in trip_code: yyyy = "2013"
            elif "2015" in trip_code: yyyy = "2015"
            elif "2025" in trip_code: yyyy = "2025"
            
            target_dir = os.path.join(r"F:\\", yyyy, "05-Mayo" if "2023" in yyyy else "07-Julio")
            os.makedirs(target_dir, exist_ok=True)
            
            base, ext = os.path.splitext(f)
            if tag not in base:
                new_f = f"{base}_{tag}{ext}"
            else:
                new_f = f
            new_p = os.path.join(target_dir, new_f)
            
            if os.path.exists(p):
                if not os.path.exists(new_p):
                    shutil.move(p, new_p)
                else:
                    os.remove(p)
                p = new_p
        
        if os.path.exists(p):
            d, f = os.path.dirname(p), os.path.basename(p)
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
            tagged_count += 1
            
    print(f"Viaje {trip_code} ({tag}): {tagged_count} archivos procesados/etiquetados.")

conn.commit()
conn.close()
print("¡Proceso de etiquetado definitivo finalizado!")
