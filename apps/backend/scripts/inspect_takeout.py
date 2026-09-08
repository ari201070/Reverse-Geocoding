import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

takeout_dir = r"F:\copia de los datos de Google\Takeout"

print("--- ESCANEANDO CONTENIDO EN F:\\copia de los datos de Google\\Takeout ---")
if os.path.exists(takeout_dir):
    items = os.listdir(takeout_dir)
    print(f"Total elementos en Takeout: {len(items)}")
    for item in items:
        p = os.path.join(takeout_dir, item)
        if os.path.isdir(p):
            # Count files inside
            fc = sum(len(files) for _, _, files in os.walk(p))
            print(f"Directorio: {item} ({fc} archivos)")
        else:
            print(f"Archivo: {item}")
