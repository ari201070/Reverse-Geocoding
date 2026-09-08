import os
import sys
import io
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

base_dir = r"F:\\"

print("--- ELIMINANDO CARPETAS VACIAS EN F: ---")
deleted_count = 0

# Run multiple passes to handle nested empty directories
for pass_num in range(3):
    empty_dirs = []
    for root, dirs, files in os.walk(base_dir, topdown=False):
        if ".Papelera_Deduplicacion" in root or "$RECYCLE.BIN" in root or "System Volume Information" in root or "LM Studio" in root:
            continue
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    empty_dirs.append(dir_path)
            except Exception:
                pass

    if not empty_dirs:
        break

    for ed in empty_dirs:
        try:
            os.rmdir(ed)
            print(f"Eliminada: {ed}")
            deleted_count += 1
        except Exception as e:
            print(f"No se pudo eliminar {ed}: {e}")

print(f"\nTotal carpetas vacias eliminadas: {deleted_count}")
