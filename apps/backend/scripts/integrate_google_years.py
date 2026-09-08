import os
import shutil
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

google_dir = r"F:\copia de los datos de Google"
years = ["2019", "2023", "2024", "2025", "2026"]

print("--- INTEGRANDO ARCHIVOS DE COPIA DE GOOGLE A CARPETAS PRINCIPALES ---")
copied_count = 0

for y in years:
    yp = os.path.join(google_dir, y)
    if not os.path.exists(yp):
        continue
    for root, dirs, files in os.walk(yp):
        for f in files:
            # Skip json or metadata files if any exist here
            if f.endswith(".json") or f.endswith(".metadata"):
                continue
            src_path = os.path.join(root, f)
            
            # Relative path inside year folder, e.g. "07-Julio/file.mp4"
            rel = os.path.relpath(src_path, yp)
            
            # Destination under F:\2019\, F:\2023\, etc.
            dest_folder = os.path.join(r"F:\\", y, os.path.dirname(rel))
            os.makedirs(dest_folder, exist_ok=True)
            
            dest_path = os.path.join(dest_folder, f)
            
            # Copy if not exists or if sizes differ
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
                print(f"Copiado: {src_path} -> {dest_path}")
                copied_count += 1
            else:
                # If exists, check size/name, handle safely
                base, ext = os.path.splitext(f)
                alt_dest = os.path.join(dest_folder, f"{base}_goog{ext}")
                if not os.path.exists(alt_dest):
                    shutil.copy2(src_path, alt_dest)
                    print(f"Copiado (alt): {src_path} -> {alt_dest}")
                    copied_count += 1

print(f"\nTotal de archivos integrados a carpetas principales: {copied_count}")
