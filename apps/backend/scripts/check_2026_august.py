import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

root = r"F:\\2026\\08-Agosto"
if os.path.exists(root):
    files = os.listdir(root)
    print(f"Archivos en 2026\\08-Agosto: {len(files)}")
    for f in files[:20]:
        print(" -", f)
