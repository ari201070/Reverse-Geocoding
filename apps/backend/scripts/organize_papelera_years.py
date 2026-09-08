import os
import sys
import io
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

papelera_base = r"F:\.Papelera_Deduplicacion"
archived_folder = os.path.join(papelera_base, "Archived_Files")

print("--- CLASIFICANDO ARCHIVOS ARCHIVADOS POR AÑO ---")

if os.path.exists(archived_folder):
    files = os.listdir(archived_folder)
    moved = 0
    for f in files:
        src = os.path.join(archived_folder, f)
        if os.path.isfile(src):
            # Try to determine year from filename prefix (e.g. 20140110..., 2023..., IMG-2023...)
            year = "Desconocido"
            if len(f) >= 4 and f[:4].isdigit() and 1980 <= int(f[:4]) <= 2030:
                year = f[:4]
            elif "2013" in f:
                year = "2013"
            elif "2014" in f:
                year = "2014"
            elif "2023" in f:
                year = "2023"
            elif "2025" in f:
                year = "2025"
            
            dest_dir = os.path.join(papelera_base, year)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, f)
            
            shutil.move(src, dest)
            moved += 1
            
    # Remove Archived_Files if empty
    try:
        os.rmdir(archived_folder)
    except Exception:
        pass
        
    print(f"Total archivos clasificados por año: {moved}")

# Final cleanup of empty dirs
for pass_num in range(3):
    for root, dirs, files in os.walk(papelera_base, topdown=False):
        for d in dirs:
            dp = os.path.join(root, d)
            try:
                if not os.listdir(dp):
                    os.rmdir(dp)
            except Exception:
                pass
