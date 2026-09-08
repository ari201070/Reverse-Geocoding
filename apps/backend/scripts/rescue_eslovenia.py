import os
import sys
import io
import shutil
import hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"
eslovenia_dir = r"F:\Fotos_Organizadas\Viajes\Eslovenia_2015"

def file_hash(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

print("--- AUDITORÍA Y RESCATE DE F:\Fotos_Organizadas\Viajes\Eslovenia_2015 ---")

# 1. 2015-07 contains actual Eslovenia trip photos -> move to F:\2015\07-Julio (or Eslovenia main travel folder)
target_eslovenia_main = os.path.join(root_drive, "2015", "07-Julio")
os.makedirs(target_eslovenia_main, exist_ok=True)

july_dir = os.path.join(eslovenia_dir, "2015-07")
moved_photos = 0
deleted_dups = 0

if os.path.exists(july_dir):
    for f in os.listdir(july_dir):
        src = os.path.join(july_dir, f)
        if os.path.isfile(src):
            dest = os.path.join(target_eslovenia_main, f)
            if os.path.exists(dest):
                if file_hash(src) == file_hash(dest):
                    os.remove(src)
                    deleted_dups += 1
                else:
                    base, ext = os.path.splitext(f)
                    dest = os.path.join(target_eslovenia_main, f"{base}_esl{ext}")
                    shutil.move(src, dest)
                    moved_photos += 1
            else:
                shutil.move(src, dest)
                moved_photos += 1

print(f"Eslovenia 2015 (Julio): {moved_photos} fotos movidas a F:\\2015\\07-Julio, {deleted_dups} duplicados eliminados.")

# 2. Inspect and classify other folders in Eslovenia_2015 (wallpapers, documents, etc.)
other_dirs = [d for d in os.listdir(eslovenia_dir) if os.path.isdir(os.path.join(eslovenia_dir, d)) and d != "2015-07"]
doc_target_dir = os.path.join(root_drive, "Documentos_Viaje", "2015", "Eslovenia")
os.makedirs(doc_target_dir, exist_ok=True)

doc_moved = 0
for od in other_dirs:
    od_path = os.path.join(eslovenia_dir, od)
    for root, _, files in os.walk(od_path):
        for f in files:
            src = os.path.join(root, f)
            dest = os.path.join(doc_target_dir, f)
            if os.path.exists(dest):
                os.remove(src)
            else:
                shutil.move(src, dest)
                doc_moved += 1

print(f"Documentos / Referencias de Eslovenia rescatados: {doc_moved} archivos movidos a {doc_target_dir}.")

# Remove Eslovenia_2015 folder if empty
shutil.rmtree(eslovenia_dir, ignore_errors=True)
print("Carpeta Eslovenia_2015 depurada y eliminada.")
