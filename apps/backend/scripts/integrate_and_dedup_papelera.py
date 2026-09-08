import os
import sys
import io
import shutil
import hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

papelera_base = r"F:\.Papelera_Deduplicacion"
root_drive = r"F:\\"

print("--- INTEGRANDO Y DESDUPLICANDO PAPELERA A CARPETAS PRINCIPALES DE AÑOS ---")

def file_hash(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

moved_count = 0
deleted_duplicates = 0

for year_folder in os.listdir(papelera_base):
    year_path = os.path.join(papelera_base, year_folder)
    if not os.path.isdir(year_path) or year_folder == "Desconocido":
        continue
    
    year = year_folder
    target_year_dir = os.path.join(root_drive, year)
    os.makedirs(target_year_dir, exist_ok=True)
    
    # Walk through files in papalera year folder
    for root, dirs, files in os.walk(year_path):
        for f in files:
            src_file = os.path.join(root, f)
            
            # Determine subfolder if any (e.g. month folder)
            rel_path = os.path.relpath(root, year_path)
            if rel_path == ".":
                # Try to guess month from filename or default to 01-Enero / general
                dest_sub = target_year_dir
            else:
                dest_sub = os.path.join(target_year_dir, rel_path)
            
            os.makedirs(dest_sub, exist_ok=True)
            dest_file = os.path.join(dest_sub, f)
            
            # Check if destination already exists (exact name or duplicate)
            if os.path.exists(dest_file):
                # Compare hashes
                h_src = file_hash(src_file)
                h_dest = file_hash(dest_file)
                if h_src and h_dest and h_src == h_dest:
                    os.remove(src_file)
                    deleted_duplicates += 1
                    continue
                else:
                    # Same name, different content -> rename with suffix
                    base, ext = os.path.splitext(f)
                    dest_file = os.path.join(dest_sub, f"{base}_dup{ext}")
            
            # Move file to main year folder
            shutil.move(src_file, dest_file)
            moved_count += 1

print(f"\nArchivos movidos/integrados a carpetas de años principales: {moved_count}")
print(f"Duplicados exactos eliminados definitivamente: {deleted_duplicates}")

# Clean up papelera year folders
shutil.rmtree(papelera_base, ignore_errors=True)
print("Papelera de deduplicación vaciada y eliminada por completo.")
