import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

eslovenia_dir = r"F:\Fotos_Organizadas\Viajes\Eslovenia_2015"

print(f"--- CONTENIDO DE {eslovenia_dir} ---")
if os.path.exists(eslovenia_dir):
    for root, dirs, files in os.walk(eslovenia_dir):
        level = root.replace(eslovenia_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/ ({len(files)} archivos)")
        for f in files[:15]:
            print(f"{indent}    - {f}")
        if len(files) > 15:
            print(f"{indent}    - ... y {len(files)-15} archivos más")
else:
    print("La carpeta no existe.")
