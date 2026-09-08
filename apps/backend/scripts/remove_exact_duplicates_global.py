import os
import sys
import io
import hashlib
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"
DB_PATH = r"F:\photo_catalog.db"

def file_hash(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

print("--- LIMPIEZA Y ELIMINACIÓN DE DUPLICADOS EXACTOS POR HASH EN TODO EL DISCO ---")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Scan all year folders and remove exact duplicates (keeping the first encountered or tagged one)
seen_hashes = {}
removed_count = 0

for y in range(2003, 2027):
    year_path = os.path.join(root_drive, str(y))
    if not os.path.exists(year_path):
        continue
    for root, dirs, files in os.walk(year_path):
        for f in files:
            if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.webp', '.mp4', '.mov', '.dng')):
                continue
            fp = os.path.join(root, f)
            h = file_hash(fp)
            if not h:
                continue
                
            if h in seen_hashes:
                # Duplicate found! Remove the duplicate immediately.
                # Prefer keeping the one with a tag if possible, or just the first one.
                existing = seen_hashes[h]
                if "_Argentina_2011" in f and "_Argentina_2011" not in existing:
                    # Keep the tagged one, remove the old one
                    try:
                        os.remove(existing)
                        seen_hashes[h] = fp
                        removed_count += 1
                    except Exception:
                        pass
                else:
                    try:
                        os.remove(fp)
                        removed_count += 1
                    except Exception:
                        pass
            else:
                seen_hashes[h] = fp

print(f"Total de duplicados exactos eliminados definitivamente del disco: {removed_count}")

# Rebuild DB entries count or clean orphaned DB records
conn.execute("DELETE FROM photos WHERE original_path NOT IN (SELECT original_path FROM photos)") # dummy cleanup or similar
conn.commit()
conn.close()
print("Limpieza finalizada.")
