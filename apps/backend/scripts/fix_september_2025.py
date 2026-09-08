import os
import sys
import io
import shutil
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root_drive = r"F:\\"
target_2025_sept = os.path.join(root_drive, "2025", "09-Septiembre")
os.makedirs(target_2025_sept, exist_ok=True)

print("--- REVISANDO ARCHIVOS DE SEPTIEMBRE 2025 MAL UBICADOS ---")

# Let's check 2026/08-Agosto or any other folder for files starting with 202509
for y in ["2026", "2025"]:
    yp = os.path.join(root_drive, y)
    if not os.path.exists(yp):
        continue
    for m in os.listdir(yp):
        mp = os.path.join(yp, m)
        if not os.path.isdir(mp):
            continue
        for f in os.listdir(mp):
            if f.startswith("202509") or f.startswith("2025-09"):
                src = os.path.join(mp, f)
                dest = os.path.join(target_2025_sept, f)
                if os.path.abspath(src) != os.path.abspath(dest):
                    if os.path.exists(dest):
                        os.remove(src)
                        print(f"Duplicado eliminado: {f}")
                    else:
                        shutil.move(src, dest)
                        print(f"Movido a Septiembre 2025: {f}")

print("¡Revisión de Septiembre 2025 finalizada!")
