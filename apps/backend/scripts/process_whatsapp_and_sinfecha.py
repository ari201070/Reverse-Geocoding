import os
import sys
import io
import shutil
import hashlib
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"

def file_hash(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

print("--- 1. PROCESANDO Y DEPURANDO F:\\S24 FE\\WhatsApp Images ---")
whatsapp_s24 = r"F:\S24 FE\WhatsApp Images"
if os.path.exists(whatsapp_s24):
    # Check if files are already elsewhere or integrate/dedup
    # Let's count how many files
    files = []
    for r, ds, fs in os.walk(whatsapp_s24):
        for f in fs:
            files.append(os.path.join(r, f))
    print(f"Archivos en WhatsApp Images S24 FE: {len(files)}")
    
    # We can integrate them into F:\2024 / 2025 / 2026 based on their names / dates or just delete if they exist
    migrated = 0
    deleted_dup = 0
    for fp in files:
        fname = os.path.basename(fp)
        # Try extract date from WhatsApp name e.g. IMG-20251011-WA0002.jpg -> 2025
        match = re.search(r'(20\d{2})(\d{2})(\d{2})', fname)
        if match:
            yyyy, mm, dd = match.groups()
            month_names = {
                "01": "01-Enero", "02": "02-Febrero", "03": "03-Marzo", "04": "04-Abril",
                "05": "05-Mayo", "06": "06-Junio", "07": "07-Julio", "08": "08-Agosto",
                "09": "09-Septiembre", "10": "10-Octubre", "11": "11-Noviembre", "12": "12-Diciembre"
            }
            m_folder = month_names.get(mm, "01-Enero")
            target_dir = os.path.join(root_drive, yyyy, m_folder)
        else:
            target_dir = os.path.join(root_drive, "SinFecha_WhatsApp")
            
        os.makedirs(target_dir, exist_ok=True)
        dest_path = os.path.join(target_dir, fname)
        
        if os.path.exists(dest_path):
            if file_hash(fp) == file_hash(dest_path):
                os.remove(fp)
                deleted_dup += 1
                continue
            else:
                base, ext = os.path.splitext(fname)
                dest_path = os.path.join(target_dir, f"{base}_s24{ext}")
                
        shutil.move(fp, dest_path)
        migrated += 1
        
    print(f"WhatsApp S24 FE: {migrated} movidos, {deleted_dup} duplicados eliminados.")
    # Remove empty folder
    shutil.rmtree(r"F:\S24 FE", ignore_errors=True)
    print("Carpeta S24 FE eliminada por completo.")

print("\n--- 2. PROCESANDO F:\\SinFecha ---")
sin_fecha_dir = r"F:\SinFecha"
if os.path.exists(sin_fecha_dir):
    sf_files = []
    for r, ds, fs in os.walk(sin_fecha_dir):
        for f in fs:
            sf_files.append(os.path.join(r, f))
            
    print(f"Archivos en F:\\SinFecha: {len(sf_files)}")
    sf_migrated = 0
    sf_deleted = 0
    
    for fp in sf_files:
        fname = os.path.basename(fp)
        # Check WhatsApp pattern IMG-YYYYMMDD-WA...
        match = re.search(r'IMG-(20\d{2})(\d{2})(\d{2})-WA', fname)
        if match:
            yyyy, mm, dd = match.groups()
            month_names = {
                "01": "01-Enero", "02": "02-Febrero", "03": "03-Marzo", "04": "04-Abril",
                "05": "05-Mayo", "06": "06-Junio", "07": "07-Julio", "08": "08-Agosto",
                "09": "09-Septiembre", "10": "10-Octubre", "11": "11-Noviembre", "12": "12-Diciembre"
            }
            m_folder = month_names.get(mm, "01-Enero")
            target_dir = os.path.join(root_drive, yyyy, m_folder)
        else:
            # Fallback for other patterns or unparsed names
            target_dir = os.path.join(root_drive, "SinFecha_Desconocido")
            
        os.makedirs(target_dir, exist_ok=True)
        dest_path = os.path.join(target_dir, fname)
        
        if os.path.exists(dest_path):
            if file_hash(fp) == file_hash(dest_path):
                os.remove(fp)
                sf_deleted += 1
                continue
            else:
                base, ext = os.path.splitext(fname)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    counter += 1
                    
        shutil.move(fp, dest_path)
        sf_migrated += 1
        
    print(f"SinFecha: {sf_migrated} integrados, {sf_deleted} duplicados eliminados.")
    shutil.rmtree(sin_fecha_dir, ignore_errors=True)
    print("Carpeta SinFecha eliminada por completo.")
