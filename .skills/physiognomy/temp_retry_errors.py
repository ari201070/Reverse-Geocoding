import sys
import json
import os
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

folder = 'F:/2023/10-Octubre'
queue = {q['filename']: q for q in
         json.load(open('data/sync_queue.json', encoding='utf-8'))}

retry = ['2023-10-04 11.19.28_IMG_20231004_111928.jpg',
         '2023-10-06 10.34.32_IMG_20231006_103432.jpg',
         '2023-10-06 10.58.52_IMG_20231006_105852.jpg',
         '2023-10-10 15.04.55_IMG_20231010_150455.jpg',
         '2023-10-10 16.11.50_IMG_20231010_161150.jpg',
         '2023-10-10 16.24.40_IMG_20231010_162440.jpg',
         '20231003_174024.jpg',
         '20231004_160455.jpg',
         '20231004_185221.jpg',
         '20231005_180806.jpg',
         '20231005_193237.jpg']

logf = open('data/sync_progress.jsonl', 'a', encoding='utf-8')
for fn in retry:
    item = queue[fn]
    fp = os.path.join(folder, fn)
    lat, lon, loc = item['lat'], item['lon'], item['loc']
    h3v = item['h3'] or '891e8052a27ffff'
    meta = {'place': loc, 'evento': 'viaje_italia_2023', 'metodo': 'SYNC_BD_DISCO_RETRY'}
    comment = 'Motor Refactorizado v2.0 | H3: ' + h3v + ' | ' + json.dumps(meta, ensure_ascii=False)
    cmd = ['exiftool', '-overwrite_original',
           '-GPSLatitude=' + str(lat), '-GPSLongitude=' + str(lon),
           '-GPSLatitudeRef=' + ('N' if lat >= 0 else 'S'),
           '-GPSLongitudeRef=' + ('E' if lon >= 0 else 'W'),
           '-ImageDescription=' + loc, '-UserComment=' + comment, fp]
    try:
        w = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        status = 'OK_RETRY' if w.returncode == 0 else 'EXIF_ERROR2'
    except Exception:
        status = 'TIMEOUT2'
    logf.write(json.dumps({'file': fn, 'status': status}) + '\n')
    logf.flush()
    print(fn, '->', status, flush=True)
logf.close()
