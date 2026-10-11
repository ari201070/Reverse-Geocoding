import sys
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout.reconfigure(encoding='utf-8')

filepath = r"F:\2025\Septiembre\Viaje Familiar de 30 dias por Argentina\יום 1 - בואנוס איירס Palermo\2025-09-27 10.06.35_20250927_100635.jpg"

print(f"Analizando archivo: {filepath}")
print(f"Existe en disco: {os.path.exists(filepath)}")

def convert_to_degrees(value):
    d = value[0]
    m = value[1]
    s = value[2]
    return d + (m / 60.0) + (s / 3600.0)

if os.path.exists(filepath):
    try:
        img = Image.open(filepath)
        exif = img._getexif()
        dt = "No disponible"
        lat, lon = None, None
        
        if exif:
            for tag_id, val in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    dt = val
                if tag == 'GPSInfo':
                    gps_data = {}
                    for t in val:
                        sub_tag = GPSTAGS.get(t, t)
                        gps_data[sub_tag] = val[t]
                    
                    lat_val = gps_data.get('GPSLatitude')
                    lat_ref = gps_data.get('GPSLatitudeRef')
                    lon_val = gps_data.get('GPSLongitude')
                    lon_ref = gps_data.get('GPSLongitudeRef')
                    
                    if lat_val and lat_ref:
                        lat = convert_to_degrees(lat_val)
                        if lat_ref != 'N':
                            lat = -lat
                    if lon_val and lon_ref:
                        lon = convert_to_degrees(lon_val)
                        if lon_ref != 'E':
                            lon = -lon

        print("\n=== FICHA TÉCNICA EXIF ===")
        print(f"Fecha y Hora del Disparo (DateTimeOriginal): {dt}")
        print(f"Latitud GPS: {lat}")
        print(f"Longitud GPS: {lon}")
    except Exception as e:
        print(f"Error procesando EXIF: {e}")
else:
    print("El archivo especificado no se encuentra en la ruta.")
