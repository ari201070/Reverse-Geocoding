import os
import sys
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout.reconfigure(encoding='utf-8')

folder = r"F:\2025\Septiembre\Viaje Familiar de 30 dias por Argentina\יום 1 - בואנוס איירס Palermo"

def convert_to_degress(value):
    d = value[0]
    m = value[1]
    s = value[2]
    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(gps_info):
    lat = None
    lon = None
    if gps_info:
        lat_val = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef')
        lon_val = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef')
        
        if lat_val and lat_ref:
            lat = convert_to_degress(lat_val)
            if lat_ref != 'N':
                lat = -lat
        if lon_val and lon_ref:
            lon = convert_to_degress(lon_val)
            if lon_ref != 'E':
                lon = -lon
    return lat, lon

print(f"Escaneando carpeta: {folder}\n")

if os.path.exists(folder):
    for f in sorted(os.listdir(folder)):
        if f.lower().endswith(('.jpg', '.jpeg', '.heic', '.png')):
            path = os.path.join(folder, f)
            try:
                img = Image.open(path)
                exif = img._getexif()
                dt = "Sin fecha EXIF"
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
                            lat, lon = get_lat_lon(gps_data)
                            
                print(f"Archivo: {f}")
                print(f"  DateTimeOriginal: {dt}")
                print(f"  GPS: Lat {lat}, Lon {lon}")
                print("-" * 50)
            except Exception as e:
                print(f"Archivo: {f} | Error leyendo EXIF: {e}")
