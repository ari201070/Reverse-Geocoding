import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

google_photos_dir = r"F:\copia de los datos de Google\Takeout\Google Fotos"

print("--- ANALIZANDO SUBDIRECTORIOS EN Google Fotos ---")
subdirs = os.listdir(google_photos_dir)
print(f"Total carpetas / álbumes / fechas en Google Fotos Takeout: {len(subdirs)}")

# Sample some folder names
for sd in subdirs[:30]:
    print(" -", sd)
