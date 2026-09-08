import os
import sys
import io
import hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

target_dir = r"F:\2011\11-Noviembre"
print("--- LIMPIEZA RÁPIDA DE DUPLICADOS EN 11-Noviembre ---")

files = os.listdir(target_dir)
hashes = {}
removed = 0

for f in files:
    fp = os.path.join(target_dir, f)
    if os.path.isfile(fp):
        try:
            with open(fp, "rb") as file_obj:
                h = hashlib.md5(file_obj.read()).hexdigest()
            if h in hashes:
                os.remove(fp)
                removed += 1
            else:
                hashes[h] = fp
        except Exception:
            pass

print(f"Eliminados: {removed}")
