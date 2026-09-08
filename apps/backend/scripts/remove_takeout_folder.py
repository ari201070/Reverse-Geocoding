import shutil
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

takeout_dir = r"F:\copia de los datos de Google\Takeout"

print(f"--- ELIMINANDO CARPETA TAKEOUT: {takeout_dir} ---")
try:
    shutil.rmtree(takeout_dir)
    print("¡Carpeta Takeout eliminada con éxito!")
except Exception as e:
    print(f"Error al eliminar Takeout: {e}")
