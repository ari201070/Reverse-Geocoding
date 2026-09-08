import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

google_dir = r"F:\copia de los datos de Google"
years = ["2019", "2023", "2024", "2025", "2026"]

for y in years:
    yp = os.path.join(google_dir, y)
    if os.path.exists(yp):
        print(f"\n--- Contenido de {y} ---")
        for root, dirs, files in os.walk(yp):
            for f in files:
                print(os.path.join(root, f))
