import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

print("--- BUSCANDO CARPETAS CON POSIBLE NOMBRE DE PAÍS O CIUDAD (ej. 2024, Copenhague, etc.) ---")

keywords = ["copenhagen", "kobenhavn", "danmark", "denmark", "2024", "escandinavia", "scandinavia", "norte"]

found = []
for root, dirs, files in os.walk(r"F:\\"):
    if ".Papelera" in root or "System Volume Information" in root or "Fotos_Organizadas" in root:
        continue
    for d in dirs:
        dl = d.lower()
        if any(k in dl for k in keywords):
            found.append(os.path.join(root, d))
    for f in files:
        fl = f.lower()
        if any(k in fl for k in keywords):
            found.append(os.path.join(root, f))

for item in found[:30]:
    print(item)
print(f"Total encontrados: {len(found)}")
