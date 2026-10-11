import sys
import json
import os
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

folder = 'F:/2023/10-Octubre'
queue = {q['filename']: q for q in
         json.load(open('data/sync_queue.json', encoding='utf-8'))}

videos = ['2023-10-04 16.32.23_VID_20231004_163223.mp4',
          '2023-10-04 16.36.25_VID_20231004_163625.mp4',
          '2023-10-04 16.37.19_VID_20231004_163719.mp4',
          '2023-10-04 17.00.40_VID_20231004_170040.mp4',
          '2023-10-06 10.36.33.mp4',
          '2023-10-06 13.16.14_VID_20231006_131614.mp4',
          '2023-10-06 15.42.18_VID_20231006_154218.mp4',
          '2023-10-06 15.43.59_VID_20231006_154359.mp4',
          '2023-10-07 19.37.02_VID_20231007_193702.mp4',
          '2023-10-07 19.39.25_VID_20231007_193925.mp4',
          '2023-10-07 19.39.50_VID_20231007_193950.mp4',
          '2023-10-07 19.42.28_VID_20231007_194228.mp4',
          '2023-10-07 19.45.43_VID_20231007_194543.mp4',
          '2023-10-07 19.49.19_VID_20231007_194919.mp4',
          '2023-10-07 19.55.14_VID_20231007_195514.mp4',
          '2023-10-07 19.57.18_VID_20231007_195718.mp4']

logf = open('data/sync_progress.jsonl', 'a', encoding='utf-8')
for fn in videos:
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
        w = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
        status = 'OK_VIDEO' if w.returncode == 0 else 'EXIF_ERROR'
    except Exception:
        status = 'TIMEOUT'
    logf.write(json.dumps({'file': fn, 'status': status}) + '\n')
    logf.flush()
logf.close()
open('data/videos_done.marker', 'w').write('done')
