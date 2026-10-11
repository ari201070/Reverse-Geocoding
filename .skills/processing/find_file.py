import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout.reconfigure(encoding='utf-8')

target = "2025-09-27 10.06.35_20250927_100635.jpg"
root_dir = r"F:\2025\Septiembre"

print(f"Buscando '{target}' en {root_dir}...")

found_path = None
for root, dirs, files in os.walk(root_dir):
    if target in files:
        found_path = os.path.join(root, target)
        break

if found_path:
    print(f"¡Encontrado en: {found_path}")
else:
    print("No se encontró en Septiembre. Buscando en todo F:/2025...")
    for root, dirs, files in os.walk(r"F:\2025"):
        if target in files:
            found_path = os.path.join(root, target)
            break
    if found_path:
        print(f"¡Encontrado en F:/2025: {found_path}")
    else:
        print("No se encontró en F:/2025.")
