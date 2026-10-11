import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import re
from datetime import datetime

lines = open('data/audit_october_real_metadata.md', encoding='utf-8').readlines()

def dms(s):
    m = re.match(r"(\d+) deg (\d+)' ([\d.]+)", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60 + float(m.group(3)) / 3600
    return None

def ts(fn):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})[ _](\d{2})[.:](\d{2})[.:](\d{2})', fn)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)), int(m.group(5)), int(m.group(6)))
    return None

fotos = []
for ln in lines:
    p = ln.strip().split('\t')
    if len(p) >= 4:
        fotos.append({'fn': p[0], 'lat': dms(p[1]), 'lon': dms(p[2]), 'desc': p[3], 'ts': ts(p[0])})

fr = [f for f in fotos if f['ts'] and f['ts'].year == 2023 and f['ts'].month == 10 and 2 <= f['ts'].day <= 12]
cg = [f for f in fr if f['lat'] is not None]
sg = [f for f in fr if f['lat'] is None]
out = []
for s in sg:
    best = None
    bt = 1e9
    for c in cg:
        d = abs((s['ts'] - c['ts']).total_seconds())
        if d <= 900 and d < bt:
            best = c
            bt = d
    if best is None:
        out.append(s['fn'])

print('SIN_ANCLA_TOTAL:', len(out))
open('data/aislados_24.txt', 'w', encoding='utf-8').write('\n'.join(out))
for x in out:
    print(x)
