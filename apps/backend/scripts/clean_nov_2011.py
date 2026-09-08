import os
import sys
import io
import hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

target_dir = r"F:\2011\11-Noviembre"
print(f"--- LIMPIEZA DE DUPLICADOS EN {target_dir} ---")

if not os.path.exists(target_dir):
    print("Carpeta no existe.")
    sys.exit(0)

def file_hash(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

seen = {}
removed = 0
files = sorted(os.listdir(target_dir))

for f in files:
    fp = os.path.join(target_dir, f)
    if not os.path.isfile(fp):
        continue
    h = file_hash(fp)
    if not h:
        continue
        
    if h in seen:
        # Duplicate! Keep tagged version if current has it or existing doesn't
        existing = seen[h]
        if "_Argentina_2011" in f and "_Argentina_2011" not in existing:
            os.remove(existing)
            seen[h] = fp
            removed += 1
        else:
            os.remove(fp)
            removed += 1
    else:
        seen[h] = fp

print(f"Duplicados eliminados en 11-Noviembre: {removed}")
