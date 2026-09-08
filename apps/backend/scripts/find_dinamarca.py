import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

viajes_dir = r"F:\Fotos_Organizadas\Viajes"

print("--- BUSCANDO DINAMARCA EN EL DISCO F ---")
found_dinamarca = []
for root, dirs, files in os.walk(r"F:\\"):
    for d in dirs:
        if "dinamarca" in d.lower() or "denmark" in d.lower():
            found_dinamarca.append(os.path.join(root, d))
    for f in files:
        if "dinamarca" in f.lower() or "denmark" in f.lower():
            found_dinamarca.append(os.path.join(root, f))

print(f"Coincidencias encontradas: {found_dinamarca}")

# Also list remaining folders/files inside F:\Fotos_Organizadas\Viajes
print(f"\n--- CONTENIDO ACTUAL DE {viajes_dir} ---")
for r, ds, fs in os.walk(viajes_dir, topdown=False):
    for d in ds:
        dp = os.path.join(r, d)
        try:
            if not os.listdir(dp):
                os.rmdir(dp)
                print(f"Eliminada carpeta vacía en Viajes: {dp}")
            else:
                print(f"Carpeta no vacía: {dp}")
        except Exception:
            pass
