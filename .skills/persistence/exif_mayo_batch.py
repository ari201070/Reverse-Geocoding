import os, sqlite3
from PIL import Image
import piexif
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

ROOT = 'F:/2023/05-Mayo'

def dec_to_dms(dec):
    dec = abs(dec)
    d = int(dec)
    m = int((dec - d) * 60)
    s = (dec - d - m / 60) * 3600
    return ((d, 1), (m, 1), (int(round(s * 100)), 100))

con = sqlite3.connect('data/photo_catalog.db', timeout=30)
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = con.cursor()
cur.execute("SELECT filename, latitude, longitude FROM photos WHERE filename LIKE '%_Bosnia_2023.jpg' AND trip_name='Bosnia 2023'")
rows = cur.fetchall()
print(f'a procesar: {len(rows)}', flush=True)
ok = 0
fail = 0
for i, (fn, lat, lng) in enumerate(rows):
    fp = os.path.join(ROOT, fn)
    if not os.path.exists(fp):
        continue
    if lat is None:
        continue
    try:
        exif_dict = piexif.load(fp)
        exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
        exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = dec_to_dms(lat)
        exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lng >= 0 else 'W'
        exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = dec_to_dms(lng)
        exif_dict['GPS'][piexif.GPSIFD.GPSVersionID] = (2, 3, 0, 0)
        piexif.insert(piexif.dump(exif_dict), fp)
        ok += 1
    except Exception as e:
        fail += 1
        print(f'fail {fn}: {str(e)[:80]}', flush=True)
    if (i + 1) % 20 == 0:
        print(f'progreso {i+1}/{len(rows)} ok={ok}', flush=True)
print(f'EXIF ok: {ok} fail: {fail}', flush=True)
con.close()
