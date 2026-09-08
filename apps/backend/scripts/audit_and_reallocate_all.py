import os
import sys
import io
import shutil
import re
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"

print("--- REVISIÓN Y ORGANIZACIÓN GLOBAL POR EXIF / FECHA REAL ---")

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("[!] Pillow required")
    sys.exit(1)

month_names = {
    "01": "01-Enero", "02": "02-Febrero", "03": "03-Marzo", "04": "04-Abril",
    "05": "05-Mayo", "06": "06-Junio", "07": "07-Julio", "08": "08-Agosto",
    "09": "09-Septiembre", "10": "10-Octubre", "11": "11-Noviembre", "12": "12-Diciembre"
}

def extract_date_from_file(filepath):
    # 1. Try parse from filename patterns like YYYYMMDD_HHMMSS or YYYY-MM-DD
    fname = os.path.basename(filepath)
    
    # Pattern: YYYYMMDD_HHMMSS or YYYYMMDD-HHMMSS
    m = re.search(r'(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[_T]([01]\d|2[0-3])([0-5]\d)([0-5]\d)', fname)
    if m:
        return m.group(1), m.group(2), m.group(3)
        
    # Pattern: YYYY-MM-DD
    m2 = re.search(r'(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])', fname)
    if m2:
        return m2.group(1), m2.group(2), m2.group(3)

    # 2. Try EXIF
    if filepath.lower().endswith(('.jpg', '.jpeg', '.tiff', '.webp')):
        try:
            img = Image.open(filepath)
            exif = img._getexif()
            if exif:
                decoded = {TAGS.get(k, k): v for k, v in exif.items()}
                dt = decoded.get('DateTimeOriginal') or decoded.get('DateTime')
                if dt:
                    if isinstance(dt, bytes):
                        dt = dt.decode(errors='ignore')
                    dt_str = str(dt)
                    m_exif = re.search(r'(20\d{2})[:\-](0[1-9]|1[0-2])[:\-](0[1-9]|[12]\d|3[01])', dt_str)
                    if m_exif:
                        return m_exif.group(1), m_exif.group(2), m_exif.group(3)
        except Exception:
            pass
            
    return None, None, None

moved_total = 0

# Scan all year folders and loose folders on F:\
for entry in os.listdir(root_drive):
    entry_path = os.path.join(root_drive, entry)
    if not os.path.isdir(entry_path) or entry.startswith('.') or entry == 'System Volume Information':
        continue
        
    for root, dirs, files in os.walk(entry_path):
        for f in files:
            if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.webp', '.mp4', '.mov', '.dng')):
                continue
            src_path = os.path.join(root, f)
            
            yyyy, mm, dd = extract_date_from_file(src_path)
            if yyyy and mm:
                target_month_folder = month_names.get(mm, "01-Enero")
                target_dir = os.path.join(root_drive, yyyy, target_month_folder)
                os.makedirs(target_dir, exist_ok=True)
                
                dest_path = os.path.join(target_dir, f)
                
                if os.path.abspath(src_path) != os.path.abspath(dest_path):
                    if os.path.exists(dest_path):
                        try:
                            os.remove(src_path)
                            moved_total += 1
                        except Exception:
                            pass
                    else:
                        try:
                            shutil.move(src_path, dest_path)
                            moved_total += 1
                        except Exception:
                            pass

print(f"\n¡Auditoría y reubicación por fecha real completada! Archivos organizados: {moved_total}")
