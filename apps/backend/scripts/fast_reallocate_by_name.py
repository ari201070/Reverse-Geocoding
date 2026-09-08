import os
import sys
import io
import shutil
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"

print("--- REUBICACIÓN RÁPIDA POR NOMBRE (PATRÓN YYYYMMDD) ---")

month_names = {
    "01": "01-Enero", "02": "02-Febrero", "03": "03-Marzo", "04": "04-Abril",
    "05": "05-Mayo", "06": "06-Junio", "07": "07-Julio", "08": "08-Agosto",
    "09": "09-Septiembre", "10": "10-Octubre", "11": "11-Noviembre", "12": "12-Diciembre"
}

moved = 0

for entry in os.listdir(root_drive):
    entry_path = os.path.join(root_drive, entry)
    if not os.path.isdir(entry_path) or entry.startswith('.') or entry == 'System Volume Information':
        continue
        
    for root, dirs, files in os.walk(entry_path):
        for f in files:
            src_path = os.path.join(root, f)
            
            # Match 20250928 or 2025-09-28 anywhere in filename
            m = re.search(r'(20\d{2})[\-_]?(0[1-9]|1[0-2])[\-_]?(0[1-9]|[12]\d|3[01])', f)
            if m:
                yyyy, mm, dd = m.groups()
                target_month_folder = month_names.get(mm, "01-Enero")
                target_dir = os.path.join(root_drive, yyyy, target_month_folder)
                os.makedirs(target_dir, exist_ok=True)
                
                dest_path = os.path.join(target_dir, f)
                
                if os.path.abspath(src_path) != os.path.abspath(dest_path):
                    if os.path.exists(dest_path):
                        try:
                            os.remove(src_path)
                            moved += 1
                        except Exception:
                            pass
                    else:
                        try:
                            shutil.move(src_path, dest_path)
                            moved += 1
                        except Exception:
                            pass

print(f"Total archivos reubicados por patrón de fecha en nombre: {moved}")
