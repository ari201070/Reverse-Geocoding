import json
import os
import sqlite3
import sys
import time
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.path.insert(0, 'scripts')


def safe(s):
    return str(s).encode('ascii', 'replace').decode()
from geopuzzle_poi_resolver import classify_scene, wiki_candidates

FOLDER = 'F:/2023/10-Octubre'
conn = sqlite3.connect('data/photo_catalog.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = conn.cursor()
cur.execute("SELECT id, filename, date_taken, latitude, longitude, location_name"
            ' FROM photos '
            "WHERE date_taken BETWEEN '2023-10-02 00:00:00' AND '2023-10-12 23:59:59' "
            'AND round(latitude,4)=41.9074 AND round(longitude,4)=12.4550 '
            'ORDER BY date_taken')
rows = cur.fetchall()
conn.close()
print('FOTOS_CLUSTER_VATICANO:', len(rows))

# Muestreo: 1 por ventana de 15 min, solo imagenes en disco, tope 20
buckets = {}
for r in rows:
    pid, fn, dt, lat, lon, loc = r
    if not fn.lower().endswith(('.jpg', '.jpeg')):
        continue
    if not os.path.exists(os.path.join(FOLDER, fn)):
        continue
    try:
        t = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    except Exception:
        continue
    key = t.strftime('%Y-%m-%d %H:%M')[:-1]  # bucket ~10 min
    buckets.setdefault(key, []).append(r)

sample = [v[0] for v in buckets.values()][:20]
print('MUESTRA_PILOTO:', len(sample))

proposals = []
logf = open('data/piloto_progress.jsonl', 'a', encoding='utf-8')
for pid, fn, dt, lat, lon, loc in sample:
    vis = classify_scene(os.path.join(FOLDER, fn))
    time.sleep(5)
    if 'error' in vis:
        proposals.append({'filename': fn, 'vision': vis, 'poi': None})
        logf.write(json.dumps({'file': fn, 'status': 'VISION_FALLO'}) + '\n')
        logf.flush()
        continue
    tags = ' '.join(vis.get('tags', [])).lower() + ' ' + vis.get('scene', '').lower()
    hint = ('garden' if any(k in tags for k in ['jard', 'giardin', 'garden', 'parque', 'verde', 'exterior', 'fountain', 'fuente', 'cupola', 'plaza'])
            else 'museum' if any(k in tags for k in ['museo', 'museum', 'interior', 'gallery', 'galer', 'sala', 'statue', 'estatua', 'fresco']) else None)
    name, src = wiki_candidates(lat, lon, hint)
    proposals.append({'filename': fn, 'date_taken': dt, 'vision': vis,
                      'poi': name, 'poi_source': src, 'actual_bd': loc})
    logf.write(json.dumps({'file': fn, 'status': 'OK',
                           'poi': name}) + '\n')
    logf.flush()

json.dump(proposals, open('data/piloto_vaticano.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
open('data/piloto_done.marker', 'w').write('done')
print('PROPUESTAS:', len(proposals))
