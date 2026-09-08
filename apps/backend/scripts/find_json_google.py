import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

found = []
for root, dirs, files in os.walk(r"F:\copia de los datos de Google"):
    for f in files:
        if "supplemental" in f.lower() or f.endswith(".json"):
            found.append(os.path.join(root, f))

print(f"Total archivos JSON/supplemental encontrados: {len(found)}")
for fp in found[:20]:
    print(fp)
