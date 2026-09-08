import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

print("--- BUSCANDO FOTOS EN SEPTIEMBRE 2024 ---")
sept_dir = r"F:\2024\09-Septiembre"
if os.path.exists(sept_dir):
    files = os.listdir(sept_dir)
    print(f"Total en Septiembre 2024: {len(files)}")
    for f in files[:40]:
        print(" -", f)
