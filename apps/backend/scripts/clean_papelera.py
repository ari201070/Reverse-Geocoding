import os
import sys
import io
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

papelera_base = r"F:\.Papelera_Deduplicacion"

print("--- LIMPIEZA Y REORGANIZACIÓN DE .Papelera_Deduplicacion ---")

if not os.path.exists(papelera_base):
    print("La papelera de deduplicación no existe.")
    sys.exit(0)

# 1. Delete all empty directories inside .Papelera_Deduplicacion recursively (multiple passes)
for pass_num in range(4):
    empty_count = 0
    for root, dirs, files in os.walk(papelera_base, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    empty_count += 1
            except Exception:
                pass
    print(f"Pasada {pass_num+1}: Eliminadas {empty_count} carpetas vacías.")

# 2. Inspect remaining non-empty contents
remaining_items = []
for root, dirs, files in os.walk(papelera_base):
    for f in files:
        remaining_items.append(os.path.join(root, f))
    for d in dirs:
        remaining_items.append(os.path.join(root, d))

print(f"\nTotal elementos no vacíos restantes en .Papelera_Deduplicacion: {len(remaining_items)}")
for item in remaining_items[:50]:
    print(" -", item)

# 3. If there are files remaining, let's migrate them to year-specific folders or organize them
migrated_count = 0
for root, dirs, files in os.walk(papelera_base):
    for f in files:
        src = os.path.join(root, f)
        # Try to infer year from filename or folder name
        # If no year can be inferred, place them in a general deduplication archive or F:\.Papelera_Deduplicacion\Archived
        dest_folder = os.path.join(papelera_base, "Archived_Files")
        os.makedirs(dest_folder, exist_ok=True)
        dest = os.path.join(dest_folder, f)
        if not os.path.exists(dest):
            shutil.move(src, dest)
            migrated_count += 1

print(f"\nArchivos restantes movidos a {os.path.join(papelera_base, 'Archived_Files')}: {migrated_count}")

# Final sweep of empty dirs inside .Papelera_Deduplicacion
for root, dirs, files in os.walk(papelera_base, topdown=False):
    for d in dirs:
        dir_path = os.path.join(root, d)
        try:
            if not os.listdir(dir_path) and dir_path != os.path.join(papelera_base, 'Archived_Files'):
                os.rmdir(dir_path)
        except Exception:
            pass
