import os
import io
import json
import sqlite3
import sys
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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


def ts(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


def is_anchor(r):
    return (r[3] is not None and r[4] is not None and r[6] not in
            ('HERITAGE_PUZZLE_INHERITANCE', 'HERITAGE_TEMPORAL',
             'HERENCIA_TEMPORAL', 'INHERITED'))


def score_loc(name):
    if not name:
        return 0.2
    keys = ['Basilica', 'Fontana', 'Pantheon', 'Arch', 'Vaticano', 'Trinit',
            'Pisa', 'Florence', 'Florencia', 'Milan', 'Venecia', 'Soperga',
            'Marbo', 'Navona', 'Colosseo', 'Trevi', 'Ben Gurion']
    return 1.0 if any(k in name for k in keys) else 0.2


anchors = [(ts(r[2]), r) for r in rows if is_anchor(r) and ts(r[2])]
print('ANCLAS_VALIDAS:', len(anchors))

changed = []
orphans = []
for r in rows:
    pid, fn, dt, lat, lon, loc, src = r
    if src not in ('HERITAGE_PUZZLE_INHERITANCE', 'HERITAGE_TEMPORAL',
                   'HERENCIA_TEMPORAL', 'INHERITED'):
        continue
    t = ts(dt)
    if not t:
        continue
    cands = []
    for at, ar in anchors:
        d = abs((t - at).total_seconds())
        if d <= 900:
            cands.append((score_loc(ar[5]), -d, ar))
    if not cands:
        orphans.append({'id': pid, 'filename': fn, 'date_taken': dt})
        continue
    cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = cands[0][2]
    if best[3] != lat or best[4] != lon:
        cur.execute('UPDATE photos SET latitude=?, longitude=?, lat=?, lng=?,'
                    " location_name=?, location_source='HERITAGE_STRICT_15MIN'"
                    ' WHERE id=?', (best[3], best[4], best[3], best[4], best[5], pid))
        changed.append({'id': pid, 'filename': fn, 'old': [lat, lon, loc],
                        'new': [best[3], best[4], best[5]]})

conn.commit()
json.dump(changed, open('data/faseB_changed.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(orphans, open('data/faseB_orphans.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('CAMBIADAS_ESTRICTA:', len(changed))
print('HUERFANAS_SIN_ANCLA:', len(orphans))
for o in orphans[:20]:
    print('  HUERFANA:', o['filename'], o['date_taken'])
conn.close()
