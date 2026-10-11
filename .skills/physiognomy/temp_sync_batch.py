import json
import os
import subprocess
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

offset = int(sys.argv[1]) if len(sys.argv) > 1 else 0
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10

folder = 'F:/2023/10-Octubre'
queue = json.load(open('data/sync_queue.json', encoding='utf-8'))
batch = queue[offset:offset + limit]

ok = verified = fail = 0
logf = open('data/sync_progress.jsonl', 'a', encoding='utf-8')
for item in batch:
    fn = item['filename']
    fp = os.path.join(folder, fn)
    if fn.lower().endswith('.mp4'):
        logf.write(json.dumps({'file': fn, 'status': 'SKIPPED_VIDEO'}) + '\n')
        logf.flush()
        print(fn, '-> SKIPPED_VIDEO', flush=True)
        continue
    status = 'FAIL'
    if os.path.exists(fp):
        try:
            r = subprocess.run(
                ['exiftool', '-T', '-GPSLatitude', '-GPSLongitude', fp],
                capture_output=True, text=True, timeout=20)
            parts = r.stdout.strip().split('\t')
            has_gps = len(parts) >= 1 and parts[0].strip() not in ('', '-')
            if has_gps:
                verified += 1
                status = 'VERIFIED'
            else:
                lat, lon = item['lat'], item['lon']
                loc = item['loc']
                h3v = item['h3'] or '891e8052a27ffff'
                meta = {'place': loc, 'evento': 'viaje_italia_2023', 'metodo': 'SYNC_BD_DISCO'}
                comment = 'Motor Refactorizado v2.0 | H3: ' + h3v + ' | ' + json.dumps(meta, ensure_ascii=False)
                cmd = ['exiftool', '-overwrite_original',
                       '-GPSLatitude=' + str(lat), '-GPSLongitude=' + str(lon),
                       '-GPSLatitudeRef=' + ('N' if lat >= 0 else 'S'),
                       '-GPSLongitudeRef=' + ('E' if lon >= 0 else 'W'),
                       '-ImageDescription=' + loc, '-UserComment=' + comment, fp]
                w = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if w.returncode == 0:
                    ok += 1
                    status = 'OK'
                else:
                    fail += 1
                    status = 'EXIF_ERROR'
        except Exception:
            fail += 1
            status = 'TIMEOUT'
    else:
        fail += 1
        status = 'NOT_FOUND'
    logf.write(json.dumps({'file': fn, 'status': status}) + '\n')
    logf.flush()
    print(fn, '->', status, flush=True)
logf.close()
print('LOTE offset=%d OK=%d VERIFIED=%d FAIL=%d' % (offset, ok, verified, fail), flush=True)
