import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

search_dirs = [r"F:\2015", r"F:\Fotos_Organizadas", r"F:\2013"]

print("--- BUSCANDO FOTOS DE ESLOVENIA EN EL DISCO F ---")
sample_name = "2015-07-01 22.53.17.jpg"

found_paths = []
for sd in search_dirs:
    if os.path.exists(sd):
        for root, dirs, files in os.walk(sd):
            if sample_name in files:
                found_paths.append(os.path.join(root, sample_name))

print(f"Encontradas coincidencias para {sample_name}: {found_paths}")
if not found_paths:
    print("Buscando en todo F:\\...")
    for root, dirs, files in os.walk(r"F:\\"):
        if sample_name in files:
            found_paths.append(os.path.join(root, sample_name))
            if len(found_paths) > 5: break
    print(f"Encontradas en F:\\: {found_paths}")
