import os, re, sqlite3, math
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def parse_fn(fn):
    m = re.search(r'(20\d{2})-(\d{2})-(\d{2})[ _]+(\d{2})\.(\d{2})\.(\d{2})', fn)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)))
    m2 = re.search(r'(20\d{2})(\d{2})(\d{2})', fn)
    if m2:
        return datetime(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)), 12, 0, 0)
    return None

def hav(a, b, c, d):
    R = 6371.0
    dlat = math.radians(c - a)
    dlon = math.radians(d - b)
    h = math.sin(dlat/2)**2 + math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(h))

import h3
def h3_9(lat, lng):
    return h3.latlng_to_cell(round(lat, 4), round(lng, 4), 9)

root = 'F:/2023/05-Mayo'
files = sorted(os.listdir(root))
print('archivos:', len(files), flush=True)

con = sqlite3.connect('data/photo_catalog.db', timeout=30)
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = con.cursor()

BOS_START = datetime(2023, 4, 29)
BOS_END = datetime(2023, 5, 6, 23, 59, 59)

updates = []
for fn in files:
    low = fn.lower()
    if 'recycle' in low or 'papelera' in low or 'trash' in low:
        continue
    dt = parse_fn(fn)
    if not dt:
        continue
    if not (BOS_START <= dt <= BOS_END):
        continue
    cur.execute('SELECT id, latitude, longitude, location_source FROM photos WHERE filename=?', (fn,))
    row = cur.fetchone()
    if not row:
        base = fn.replace('_Israel_2023', '').replace('_Bosnia_2023', '')
        cur.execute('SELECT id, latitude, longitude, location_source FROM photos WHERE filename=?', (base,))
        row = cur.fetchone()
    if not row:
        continue
    pid, lat, lng, src = row
    if src == 'EXIF_GPS':
        continue
    if lat is None or lng is None:
        continue
    lat4 = round(lat, 4)
    lng4 = round(lng, 4)
    h = h3_9(lat4, lng4)
    updates.append((pid, fn, lat4, lng4, h, dt))

print('candidatos:', len(updates), flush=True)
updates_sorted = sorted(updates, key=lambda x: parse_fn(x[1]))
ok_list = []
vetados = []
prev = None
for pid, fn, lat, lng, h, dt in updates_sorted:
    if prev:
        dmin = (dt - prev[5]).total_seconds() / 60
        if 0 < dmin <= 60:
            d = hav(prev[2], prev[3], lat, lng)
            v = d / (dmin / 60)
            if v > 30:
                vetados.append((prev[1], fn, round(d, 2), round(dmin, 1), round(v, 1)))
                prev = (pid, fn, lat, lng, h, dt)
                continue
    ok_list.append((pid, fn, lat, lng, h, dt))
    prev = (pid, fn, lat, lng, h, dt)

print('pasan veto:', len(ok_list), 'vetados:', len(vetados), flush=True)
for v in vetados[:5]:
    print(v, flush=True)

con.execute('BEGIN TRANSACTION')
n = 0
for pid, fn, lat, lng, h, dt in ok_list:
    cur.execute('UPDATE photos SET latitude=?, longitude=?, lat=?, lng=?, h3_index=?, trip_name=?, country=?, location_time=? WHERE id=?',
        (lat, lng, lat, lng, h, 'Bosnia 2023', 'Bosnia y Herzegovina', dt.strftime('%Y:%m:%d %H:%M:%S'), pid))
    n += 1
    if n % 1000 == 0:
        con.execute('COMMIT')
        con.execute('BEGIN TRANSACTION')
con.execute('COMMIT')
print('actualizados:', n, flush=True)
cur.execute("SELECT filename, trip_name, country, latitude, longitude, h3_index FROM photos WHERE filename='2023-05-01 08.41.30.jpg'")
print(cur.fetchone(), flush=True)
con.close()
