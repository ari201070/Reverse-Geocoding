import os
import sys
import io
import shutil
import hashlib
import sqlite3
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"
viajes_dir = r"F:\Fotos_Organizadas\Viajes"
DB_PATH = r"F:\photo_catalog.db"

def file_hash(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

# Trip mappings and target months
# Trip folder name -> (Trip Name in DB, Target Year-Month matching folder or main trip subfolder)
TRIP_MAPPINGS = {
    "Argentina_2011": {"trip_code": "argentina-2011", "tag": "Argentina_2011", "expected_ym": ["2011-11", "2011-12", "2012-01", "2012-02"]},
    "Bosnia_2023": {"trip_code": "bosnia-2023", "tag": "Bosnia_2023", "expected_ym": ["2023-04", "2023-05"]},
    "Croacia_Montenegro_2010": {"trip_code": "montenegro-2010", "tag": "Croacia_Montenegro_2010", "expected_ym": ["2010-06", "2010-07", "2010-08"]},
    "Creta_2013": {"trip_code": "creta-2013", "tag": "Creta_2013", "expected_ym": ["2013-06", "2013-07", "2013-08"]},
    "Italia_2023": {"trip_code": "italia-2023", "tag": "Italia_2023", "expected_ym": ["2023-10", "2023-11"]}
}

month_map = {
    "01": ("01-Enero", "01"), "02": ("02-Febrero", "02"), "03": ("03-Marzo", "03"), "04": ("04-Abril", "04"),
    "05": ("05-Mayo", "05"), "06": ("06-Junio", "06"), "07": ("07-Julio", "07"), "08": ("08-Agosto", "08"),
    "09": ("09-Septiembre", "09"), "10": ("10-Octubre", "10"), "11": ("11-Noviembre", "11"), "12": ("12-Diciembre", "12")
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- PROCESANDO Y REORGANIZANDO VIAJES CON TAGGING ---")

for trip_folder, info in TRIP_MAPPINGS.items():
    trip_path = os.path.join(viajes_dir, trip_folder)
    if not os.path.exists(trip_path):
        continue
        
    tag = info["tag"]
    expected_ym = info["expected_ym"]
    
    print(f"\nProcesando viaje: {trip_folder} (Tag: {tag})")
    
    for sub in os.listdir(trip_path):
        sub_path = os.path.join(trip_path, sub)
        if not os.path.isdir(sub_path):
            continue
            
        # sub is like '2011-11' or '2026-01' or 'Unknown-Unknown'
        is_trip_content = sub in expected_ym
        
        for root, _, files in os.walk(sub_path):
            for f in files:
                if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.webp', '.mp4', '.mov', '.dng')):
                    continue
                src = os.path.join(root, f)
                
                # Determine target year and month folder
                # If sub is YYYY-MM, use it. Otherwise use file date or sub
                if re.match(r'^\d{4}-\d{2}$', sub):
                    yyyy, mm = sub.split('-')
                else:
                    # fallback to file name date or default 2015-07
                    yyyy, mm = "2015", "07"
                    
                m_folder, _ = month_map.get(mm, ("01-Enero", "01"))
                target_dir = os.path.join(root_drive, yyyy, m_folder)
                os.makedirs(target_dir, exist_ok=True)
                
                base, ext = os.path.splitext(f)
                
                # Apply tag ONLY if it belongs to the trip content AND doesn't already have the tag
                if is_trip_content and not base.endswith(f"_{tag}"):
                    new_fname = f"{base}_{tag}{ext}"
                else:
                    new_fname = f
                    
                dest = os.path.join(target_dir, new_fname)
                
                if os.path.exists(dest):
                    if file_hash(src) == file_hash(dest):
                        os.remove(src)
                        continue
                    else:
                        dest = os.path.join(target_dir, f"{base}_dup{ext}")
                
                shutil.move(src, dest)
                
                # Update DB path if exists
                conn.execute("""
                    UPDATE photos 
                    SET original_path = ?, final_path = ?, trip_name = ? 
                    WHERE original_path LIKE ? OR final_path LIKE ?
                """, (dest, dest, info["trip_code"], f"%{f}%", f"%{f}%"))

conn.commit()
conn.close()

print("\n¡Proceso de reubicación y etiquetado de viajes completado con éxito!")
