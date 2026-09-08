import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

base_dir = r"F:\\"

print("--- ESCANEANDO CARPETAS VACIAS EN F: ---")
empty_dirs = []
for root, dirs, files in os.walk(base_dir, topdown=False):
    if ".Papelera_Deduplicacion" in root or "$RECYCLE.BIN" in root or "System Volume Information" in root:
        continue
    for d in dirs:
        dir_path = os.path.join(root, d)
        try:
            if not os.listdir(dir_path):
                empty_dirs.append(dir_path)
        except Exception:
            pass

print(f"Total carpetas vacias encontradas: {len(empty_dirs)}")
for ed in empty_dirs:
    print(ed)
