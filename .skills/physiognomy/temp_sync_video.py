import json
import os
import subprocess
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

fn = sys.argv[1]
folder = 'F:/2023/10-Octubre'
queue = {q['filename']: q for q in
         json.load(open('data/sync_queue.json', encoding='utf-8'))}
item = queue[fn]
fp = os.path.join(folder, fn)
lat, lon, loc = item['lat'], item['lon'], item['loc']
h3v = item['h3'] or '891e8052a27ffff'
meta = {'place': loc, 'evento': 'viaje_italia_2023', 'metodo': 'SYNC_BD_DISCO_VIDEO'}
comment = 'Motor Refactorizado v2.0 | H3: ' + h3v + ' | ' + json.dumps(meta, ensure_ascii=False)
cmd = ['exiftool', '-overwrite_original',
       '-GPSLatitude=' + str(lat), '-GPSLongitude=' + str(lon),
       '-GPSLatitudeRef=' + ('N' if lat >= 0 else 'S'),
       '-GPSLongitudeRef=' + ('E' if lon >= 0 else 'W'),
       '-ImageDescription=' + loc, '-UserComment=' + comment, fp]
try:
    w = subprocess.run(cmd, capture_output=True, text=True, timeout=110)
    status = 'OK_VIDEO' if w.returncode == 0 else 'EXIF_ERROR'
except Exception:
    status = 'TIMEOUT'
with open('data/sync_progress.jsonl', 'a', encoding='utf-8') as logf:
    logf.write(json.dumps({'file': fn, 'status': status}) + '\n')
print(fn, '->', status, flush=True)
