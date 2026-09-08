import os
import sys
import io
import shutil
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"

print("--- ESCANEANDO Y REUBICANDO FOTOS CON FECHA EXPLÍCITA EN EL NOMBRE ---")

month_names = {
    "01": "01-Enero", "02": "02-Febrero", "03": "03-Marzo", "04": "04-Abril",
    "05": "05-Mayo", "06": "06-Junio", "07": "07-Julio", "08": "08-Agosto",
    "09": "09-Septiembre", "10": "10-Octubre", "11": "11-Noviembre", "12": "12-Diciembre"
}

reallocated_count = 0

# Walk through all years and folders to find misplaced files whose names start with YYYY-MM-DD
years = [str(y) for y in range(2003, 2027)]

for y in years:
    year_dir = os.path.join(root_drive, y)
    if not os.path.exists(year_dir):
        continue
    
    for root, dirs, files in os.walk(year_dir):
        for f in files:
            src_path = os.path.join(root, f)
            
            # Match pattern like YYYY-MM-DD at the start of filename
            match = re.match(r'^(20\d{2})-(\d{2})-(\d{2})', f)
            if match:
                file_yyyy, file_mm, file_dd = match.groups()
                
                # Target correct directory: F:\YYYY\MM-NombreMes\
                target_month_folder = month_names.get(file_mm, "01-Enero")
                target_dir = os.path.join(root_drive, file_yyyy, target_month_folder)
                os.makedirs(target_dir, exist_ok=True)
                
                dest_path = os.path.join(target_dir, f)
                
                if os.path.abspath(src_path) != os.path.abspath(dest_path):
                    if os.path.exists(dest_path):
                        # If destination already exists, remove duplicate
                        os.remove(src_path)
                        reallocated_count += 1
                        print(f"Duplicado eliminado: {f}")
                    else:
                        shutil.move(src_path, dest_path)
                        reallocated_count += 1
                        print(f"Reubicada: {f} -> {file_yyyy}\\{target_month_folder}")

print(f"\nTotal de archivos reubicados/depurados por fecha en nombre: {reallocated_count}")
