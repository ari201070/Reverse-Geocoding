import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

year_2024 = r"F:\2024"

print("--- INSPECCIONANDO MESES EN F:\2024 ---")
if os.path.exists(year_2024):
    for m in os.listdir(year_2024):
        mp = os.path.join(year_2024, m)
        if os.path.isdir(mp):
            files = os.listdir(mp)
            print(f"Mes: {m} ({len(files)} archivos)")
            for f in files[:5]:
                print(f"   - {f}")
