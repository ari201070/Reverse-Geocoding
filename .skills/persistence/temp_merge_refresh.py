import os
import json
import sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

REPO = '.'


def dms(lat, lon):
    def fmt(v, pos, neg):
        d = int(abs(v))
        mf = (abs(v) - d) * 60
        m = int(mf)
        s = (mf - m) * 60
        return '%d deg %d\' %.2f" %s' % (d, m, s, pos if v >= 0 else neg)
    return fmt(lat, 'N', 'S'), fmt(lon, 'E', 'W')


# Estado final por archivo (ultima entrada del log manda)
latest = {}
for ln in open('data/sync_progress.jsonl', encoding='utf-8'):
    d = json.loads(ln)
    latest[d['file']] = d['status']

conn = sqlite3.connect('data/photo_catalog.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = conn.cursor()
cur.execute('SELECT filename, latitude, longitude, location_name FROM photos')
bd = {r[0]: (r[1], r[2], r[3]) for r in cur.fetchall()}
conn.close()

flight_label = 'Vuelo Tel Aviv-Roma (en vuelo)'
pre_label = 'Pre-viaje (anterior al itinerario Italia 02-12 Oct)'
flight_files = {'2023-10-02 11.28.01.jpg', '2023-10-02 14.54.11.jpg',
                '2023-10-02 14.54.16.jpg', '2023-10-02 14.54.20.jpg',
                '2023-10-02 14.54.25.jpg', '2023-10-02 14.55.07.jpg',
                '2023-10-02 14.58.15.jpg', '2023-10-02 14.58.17.jpg',
                '2023-10-02 14.58.20.jpg', '2023-10-02 14.58.55.jpg',
                '2023-10-02 14.59.00.jpg', '20231002_145420.jpg',
                '20231002_145507.jpg', '20231002_145817.jpg',
                '20231002_145855.jpg', '20231002_112801.jpg'}
wa_files = {'IMG-20231001-WA0000.jpeg', 'IMG-20231002-WA0000.jpeg'}
bg_files = {'2023-10-02 09.00.58.jpg', '20231002_090058.jpg'}

out = []
n_new = 0
for ln in open('data/audit_october_real_metadata_v2.md', encoding='utf-8'):
    parts = ln.rstrip('\n').split('\t')
    fn = parts[0].strip() if parts else ''
    st = latest.get(fn)
    new_line = None
    if st in ('OK', 'OK_RETRY', 'OK_VIDEO') and fn in bd and bd[fn][0] is not None:
        la, lo, nm = bd[fn]
        d1, d2 = dms(la, lo)
        new_line = '%s\t%s\t%s\t%s\n' % (fn, d1, d2, nm)
    elif fn in flight_files:
        new_line = '%s\t-\t-\t%s\n' % (fn, flight_label)
    elif fn in wa_files:
        new_line = '%s\t-\t-\t%s\n' % (fn, pre_label)
    elif fn in bg_files:
        d1, d2 = dms(32.0094, 34.8828)
        new_line = '%s\t%s\t%s\t%s\n' % (fn, d1, d2, 'Aeropuerto Ben Gurion, Tel Aviv, Israel')
    if new_line is not None:
        out.append(new_line)
        n_new += 1
    else:
        out.append(ln if ln.endswith('\n') else ln + '\n')

open('data/audit_october_real_metadata.md', 'w', encoding='utf-8').writelines(out)
print('LINEAS:', len(out), 'ACTUALIZADAS:', n_new)

con = sum(1 for ln in out if not ln.split('\t')[1].strip().startswith('-'))
print('CON_GPS:', con, 'SIN_GPS:', len(out) - con)
