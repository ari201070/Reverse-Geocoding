import os
import io
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
conn.close()


def ts(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


# Recorrer en orden cronologico llevando la ultima ancla valida
# (ancla = con GPS y source NO heredado)
last_anchor = None
suspects = []
heritage_total = 0
for r in rows:
    pid, fn, dt, lat, lon, loc, src = r
    t = ts(dt) if dt else None
    inherited = src in ('HERITAGE_PUZZLE_INHERITANCE', 'HERITAGE_TEMPORAL',
                        'HERENCIA_TEMPORAL', 'INHERITED')
    if lat is not None and not inherited:
        last_anchor = (t, fn, lat, lon, loc)
    elif inherited:
        heritage_total += 1
        if last_anchor and last_anchor[0] and t:
            gap = abs((t - last_anchor[0]).total_seconds())
            if gap > 900:
                suspects.append((fn, dt, loc, last_anchor[1], gap))
        elif not last_anchor:
            suspects.append((fn, dt, loc, 'SIN_ANCLA_PREVIA', -1))

print('HEREDADAS_TOTAL:', heritage_total)
print('SOSPECHOSAS_GAP_15MIN:', len(suspects))
for s in suspects[:30]:
    print(' ', s[0], '|', s[1], '|', (s[2] or '')[:35], '| ancla:', s[3],
          '| gap_s:', int(s[4]) if s[4] >= 0 else s[4])
