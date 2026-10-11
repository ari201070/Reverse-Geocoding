import os
import sys
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Forzar utf-8 en stdout
sys.stdout.reconfigure(encoding='utf-8')

folder = r"F:\2025\Septiembre\Viaje Familiar de 30 dias por Argentina\יום 1 - בואנוס אייርס Palermo"

print(f"Carpeta: {folder}")
print(f"Existe: {os.path.exists(folder)}")

if os.path.exists(folder):
    for f in os.listdir(folder):
        if f.lower().endswith(('.jpg', '.jpeg', '.heic')):
            path = os.path.join(folder, f)
            try:
                img = Image.open(path)
                exif = img._getexif()
                dt = "Sin fecha"
                has_gps = False
                if exif:
                    for tag_id, val in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTimeOriginal':
                            dt = val
                        if tag == 'GPSInfo':
                            has_gps = True
                print(f"Archivo: {f} | Fecha: {dt} | GPS: {has_gps}")
            except Exception as e:
                print(f"Archivo: {f} | Error: {e}")
