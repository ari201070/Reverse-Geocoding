import os
import io
import json
import re
import sqlite3
import sys
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def ts_exif(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


def ts_name(fn):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})[ _](\d{2})[.:](\d{2})[.:](\d{2})', fn)
    if m:
        return datetime(*map(int, m.groups()))
    m = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', fn)
    if m:
        return datetime(*map(int, m.groups()))
    m = re.search(r'VID_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', fn)
    if m:
        return datetime(*map(int, m.groups()))
    return None


def score_loc(name):
    if not name:
        return 0.2
    keys = ['Basilica', 'Fontana', 'Pantheon', 'Arch', 'Vaticano', 'Trinit',
            'Pisa', 'Florence', 'Florencia', 'Milan', 'Venecia', 'Soperga',
            'Marbo', 'Navona', 'Colosseo', 'Trevi', 'Ben Gurion']
    return 1.0 if any(k in name for k in keys) else 0.2


conn = sqlite3.connect('data/photo_catalog.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = conn.cursor()
cur.execute("SELECT id, filename, date_taken, latitude, longitude, location_name,"
            ' location_source FROM photos '
            "WHERE date_taken BETWEEN '2023-10-02 00:00:00' AND '2023-10-12 23:59:59' "
            'ORDER BY date_taken')
rows = cur.fetchall()


def is_anchor(r):
    return (r[3] is not None and r[4] is not None and r[6] not in
            ('HERITAGE_PUZZLE_INHERITANCE', 'HERITAGE_TEMPORAL',
             'HERENCIA_TEMPORAL', 'INHERITED'))


anchors = []
for r in rows:
    if is_anchor(r):
        t = ts_name(r[1]) or ts_exif(r[2])
        if t:
            anchors.append((t, r))
print('ANCLAS_VALIDAS:', len(anchors))

orphans = json.load(open('data/faseB_orphans.json', encoding='utf-8'))
by_id = {r[0]: r for r in rows}
fixed = []
still = []
for o in orphans:
    r = by_id.get(o['id'])
    if not r:
        continue
    t = ts_name(r[1]) or ts_exif(r[2])
    if not t:
        still.append(o)
        continue
    cands = []
    for at, ar in anchors:
        if ar[0] == r[0]:
            continue
        d = abs((t - at).total_seconds())
        if d <= 900:
            cands.append((score_loc(ar[5]), -d, ar))
    if not cands:
        still.append(o)
        continue
    cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = cands[0][2]
    if best[3] != r[3] or best[4] != r[4]:
        cur.execute('UPDATE photos SET latitude=?, longitude=?, lat=?, lng=?,'
                    " location_name=?, location_source='HERITAGE_STRICT_15MIN'"
                    ' WHERE id=?', (best[3], best[4], best[3], best[4], best[5], r[0]))
        fixed.append({'id': r[0], 'filename': r[1],
                      'new': [best[3], best[4], best[5]]})

conn.commit()
old = json.load(open('data/faseB_changed.json', encoding='utf-8'))
old.extend(fixed)
json.dump(old, open('data/faseB_changed.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(still, open('data/faseB_orphans.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('FIX_HORA_NOMBRE:', len(fixed))
print('HUERFANAS_FINAL:', len(still))
for o in still[:25]:
    print('  HUERFANA:', o['filename'], o['date_taken'])
conn.close()
