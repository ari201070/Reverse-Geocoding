import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

folder = 'F:/2023/10-Octubre'
report = 'data/audit_october_real_metadata_v2.md'

disk = set(os.listdir(folder))
print('EN_DISCO:', len(disk))

lines = open(report, encoding='utf-8', errors='replace').readlines()
# Quitar ultima linea trunca (no termina en newline completo de 4 columnas)
if lines and lines[-1].count('\t') < 3:
    print('LINEA_TRUNCA_ELIMINADA:', lines[-1][:60])
    lines = lines[:-1]

rep_names = set()
for ln in lines:
    parts = ln.split('\t')
    if parts:
        rep_names.add(parts[0].strip())

missing = sorted(d for d in disk if d not in rep_names)
print('YA_EN_INFORME:', len(rep_names))
print('FALTANTES:', len(missing))
for m in missing:
    print('  PEND:', m)

open(report, 'w', encoding='utf-8').writelines(lines)
open('data/audit_missing.txt', 'w', encoding='utf-8').write('\n'.join(missing))
