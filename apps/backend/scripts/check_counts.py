import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root = r"F:\\"
for y in ["2025", "2026"]:
    yp = os.path.join(root, y)
    if os.path.exists(yp):
        print(f"Año {y}:")
        for m in sorted(os.listdir(yp)):
            mp = os.path.join(yp, m)
            if os.path.isdir(mp):
                print(f"   {m}: {len(os.listdir(mp))} archivos")
