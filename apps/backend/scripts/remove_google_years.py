import shutil
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

target_dir = r"F:\copia de los datos de Google"

print("--- ELIMINANDO CARPETAS DE AÑOS EN 'copia de los datos de Google' ---")
for y in ["2019", "2023", "2024", "2025", "2026"]:
    path = f"{target_dir}\\{y}"
    try:
        shutil.rmtree(path)
        print(f"Eliminado por completo: {path}")
    except Exception as e:
        print(f"No se pudo eliminar {path}: {e}")
