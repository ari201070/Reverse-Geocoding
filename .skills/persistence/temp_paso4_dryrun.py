"""Paso 4 adaptado a nuestro ambiente (Fase 1: solo lectura).
Herencia -> Wikipedia GeoSearch (nombres) -> Photon (fallback) -> cache.
Carga .env explicitamente (leccion aprendida: el shell no lo hereda).
"""
import json
import os
import re
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

REPO = os.path.dirname(os.path.abspath(__file__))

# 1. Cargar .env explicito
ENV = {}
with open(os.path.join(REPO, '.env'), encoding='utf-8') as f:
    for ln in f:
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            ENV[k.strip()] = v.strip()
print('ENV_KEYS:', [k for k in ENV if 'API' in k or 'MODEL' in k])

UA = {'User-Agent': 'ReverseGeocodingPhotosApp/1.0 (contact@example.com)'}


def wiki_naming(lat, lon):
    url = ('https://es.wikipedia.org/w/api.php?action=query&list=geosearch'
           '&gscoord=%s%%7C%s&gsradius=1500&gslimit=3&format=json') % (lat, lon)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        hits = data.get('query', {}).get('geosearch', [])
        return [(h['title'], h['dist']) for h in hits]
    except Exception as e:
        return [('ERROR:' + str(e), -1)]


def photon_naming(lat, lon):
    url = 'https://photon.komoot.io/reverse?lat=%s&lon=%s' % (lat, lon)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        feats = data.get('features', [])
        if feats:
            p = feats[0].get('properties', {})
            return p.get('name') or p.get('street')
        return None
    except Exception:
        return None


def ts_of(fn):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})[ _](\d{2})[.:](\d{2})[.:](\d{2})', fn)
    if m:
        return datetime(*map(int, m.groups()))
    m = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', fn)
    if m:
        return datetime(*map(int, m.groups()))
    return None


targets = ['PSX_20231006_225840.jpg',
           'IMG-20231001-WA0000.jpeg',
           '2023-10-29 18.48.28_result.jpg',
           '2023-10-30 16.31.07_0ffed33b-0593-4b26-815c-bc8f85bc60cc.jpg']

conn = sqlite3.connect(os.path.join(REPO, 'data', 'photo_catalog.db'))
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = conn.cursor()

for fn in targets:
    t = ts_of(fn)
    print('=' * 60)
    print('ARCHIVO:', fn, '| FECHA:', t)
    if not t:
        print('  PROPUESTA: sin timestamp parseable -> no tocar')
        continue
    cur.execute('SELECT filename, date_taken, latitude, longitude, location_name '
                'FROM photos WHERE latitude IS NOT NULL AND longitude IS NOT NULL')
    best = None
    best_d = float('inf')
    for r in cur.fetchall():
        try:
            dt = datetime.strptime(r[1], '%Y-%m-%d %H:%M:%S')
        except Exception:
            continue
        d = abs((t - dt).total_seconds())
        if d < best_d:
            best_d = d
            best = r
    if best and best_d <= 900:
        print('  HERENCIA: %s (%.0fs) -> %s,%s %s'
              % (best[0], best_d, best[2], best[3], best[4]))
        names = wiki_naming(best[2], best[3])
        print('  WIKIPEDIA:', names[0] if names else None)
    else:
        print('  HERENCIA: sin ancla a <=15min (mejor: %s a %.0fs)'
              % (best[0] if best else None, best_d))
        print('  PROPUESTA: no tocar en esta fase (requiere vision OpenRouter)')

conn.close()
