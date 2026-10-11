import os, re, sqlite3, subprocess, shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
ROOT='F:/2023/05-Mayo'
EXIFTOOL='/c/Users/flier/AppData/Local/Programs/ExifTool/exiftool'
con=sqlite3.connect('data/photo_catalog.db', timeout=30)
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur=con.cursor()
# Obtener los 105 actualizados: trip Bosnia 2023 + country Bosnia con fecha mayo y archivo en carpeta mayo
cur.execute("SELECT id, filename, latitude, longitude FROM photos WHERE trip_name='Bosnia 2023' AND country='Bosnia y Herzegovina'")
rows=cur.fetchall()
print(f'filas Bosnia en DB: {len(rows)}', flush=True)
# Filtrar solo las que corresponden a carpeta mayo por fecha 2023-05-01 a 2023-05-06
import re
from datetime import datetime
candidatos=[]
for pid, fn, lat, lng in rows:
    # buscar archivo fisico correspondiente en mayo
    # fn en DB es sin sufijo, fisico con _Israel_2023
    base=os.path.splitext(fn)[0]
    # candidatos fisicos
    for suffix in ['_Israel_2023','_Bosnia_2023','']:
        for ext in ['.jpg','.jpeg','.JPG','.JPEG','.mp4','.MP4']:
            cand=os.path.join(ROOT, base+suffix+ext)
            if os.path.exists(cand):
                candidatos.append((pid, fn, cand, lat, lng))
                break
        else:
            continue
        break
print(f'candidatos con fisico: {len(candidatos)}', flush=True)
# Deduplicar por pid
seen={}
for pid, fn, cand, lat, lng in candidatos:
    seen[pid]=(fn, cand, lat, lng)
print(f'pids unicos: {len(seen)}', flush=True)
# Fase fisica: EXIF + rename solo jpg/jpeg con GPS no nativo
con2=sqlite3.connect('data/photo_catalog.db', timeout=30)
cursor = con2.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur2=con2.cursor()
cur2.execute('BEGIN TRANSACTION')
ren=0
exif_ok=0
for pid, (fn, cand, lat, lng) in list(seen.items())[:200]:
    # verificar source no nativo
    cur2.execute('SELECT location_source FROM photos WHERE id=?', (pid,))
    src=cur2.fetchone()[0]
    if src=='EXIF_GPS':
        continue
    # 1) EXIF solo jpg/jpeg
    if cand.lower().endswith(('.jpg','.jpeg')):
        try:
            # redondeo 4 decimales ya aplicado
            cmd=[EXIFTOOL,'-overwrite_original',
                 f'-GPSLatitude={abs(lat)}', f'-GPSLatitudeRef={"N" if lat>=0 else "S"}',
                 f'-GPSLongitude={abs(lng)}', f'-GPSLongitudeRef={"E" if lng>=0 else "W"}',
                 cand]
            r=subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode==0:
                exif_ok+=1
            else:
                print(f'EXIF fail {cand}: {r.stderr[:120]}', flush=True)
        except Exception as e:
            print(f'EXIF err {cand}: {e}', flush=True)
    # 2) rename _Israel_2023 -> _Bosnia_2023
    base=os.path.basename(cand)
    if '_Israel_2023' in base:
        nuevo=base.replace('_Israel_2023','_Bosnia_2023')
        destino=os.path.join(ROOT, nuevo)
        if not os.path.exists(destino):
            try:
                os.rename(cand, destino)
                # actualizar DB filename y file_path
                cur2.execute('SELECT file_path FROM photos WHERE id=?', (pid,))
                fp=cur2.fetchone()[0] or ''
                nuevo_fp=fp.replace(fn, nuevo) if fn in fp else os.path.join(ROOT, nuevo)
                cur2.execute('UPDATE photos SET filename=?, file_path=? WHERE id=?', (nuevo, nuevo_fp, pid))
                ren+=1
            except Exception as e:
                print(f'rename err {base}: {e}', flush=True)
cur2.execute('COMMIT')
print(f'EXIF ok: {exif_ok}, renombrados: {ren}', flush=True)
# verificacion puntual
cur2.execute("SELECT filename, latitude, longitude FROM photos WHERE filename LIKE '%08.41.30%'")
print(cur2.fetchall(), flush=True)
con2.close()
con.close()
