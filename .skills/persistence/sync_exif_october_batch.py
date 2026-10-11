#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizacion EXIF Octubre 2023 - Version por lotes (clusteriza por coordenadas)
Escribe GPS + ImageDescription (city) + UserComment (H3) en JPG fisicos.
Una llamada exiftool por cluster de (lat4, lng4, city) en vez de por archivo.
"""
import os
import re
import json
import time
import sqlite3
import subprocess
import h3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

ROOT = r'F:\2023\10-Octubre'
DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
EXIFTOOL = r'C:\Users\flier\AppData\Local\Programs\ExifTool\exiftool.exe'
CHUNK = 40  # max archivos por llamada exiftool


def bulk_check_gps(files):
    """Una sola llamada exiftool: devuelve set de archivos que YA tienen GPS."""
    have = set()
    for i in range(0, len(files), 200):
        chunk = files[i:i + 200]
        try:
            r = subprocess.run(
                [EXIFTOOL, '-m', '-j', '-GPSLatitude'] + chunk,
                capture_output=True, text=True, timeout=120)
            if r.stdout.strip():
                for item in json.loads(r.stdout):
                    if 'GPSLatitude' in item:
                        have.add(os.path.normcase(item['SourceFile']))
        except Exception as e:
            print('WARN bulk check: {}'.format(e))
    return have


def write_group(files, lat, lng, city, h3_idx):
    """Escribe GPS+Descripcion+UserComment a un grupo de archivos (1 llamada)."""
    ref_lat = 'N' if lat >= 0 else 'S'
    ref_lng = 'E' if lng >= 0 else 'W'
    user_comment = 'Motor Refactorizado v1.0 | H3: {} | {}'.format(
        h3_idx,
        json.dumps({"place": city, "evento": "viaje_italia_2023"}, ensure_ascii=False))
    ok, fail = 0, []
    for i in range(0, len(files), CHUNK):
        part = files[i:i + CHUNK]
        cmd = [EXIFTOOL, '-m', '-overwrite_original',
               '-GPSLatitude={:.4f}'.format(abs(lat)),
               '-GPSLatitudeRef=' + ref_lat,
               '-GPSLongitude={:.4f}'.format(abs(lng)),
               '-GPSLongitudeRef=' + ref_lng,
               '-GPSVersionID=2 3 0 0',
               '-ImageDescription=' + city,
               '-UserComment=' + user_comment] + part
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode == 0 or 'updated' in r.stdout.lower():
                ok += len(part)
            else:
                fail.extend(part)
                print('  FAIL rc={} stdout={} stderr={}'.format(
                    r.returncode, r.stdout[:80], r.stderr[:80]))
        except Exception as e:
            fail.extend(part)
            print('  EXC: {}'.format(e))
        time.sleep(0.2)
    return ok, fail


def main():
    con = sqlite3.connect(DB_PATH, timeout=30)
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cur = con.cursor()
    cur.execute('''
        SELECT filename, latitude, longitude, city, date_source
        FROM photos
        WHERE date_taken LIKE '2023-10-%'
          AND latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY date_taken
    ''')
    rows = cur.fetchall()
    con.close()
    print('Registros DB con GPS (Oct 2023): {}'.format(len(rows)))

    # Mapa de ficheros fisicos (normalizado)
    disk = {}
    for f in os.listdir(ROOT):
        if f.lower().endswith(('.jpg', '.jpeg')):
            disk[f.lower()] = os.path.join(ROOT, f)
    print('Fisicos .jpg/.jpeg en carpeta: {}'.format(len(disk)))

    pendientes = {}  # (lat4, lng4, city) -> [fpaths]
    no_fisico = 0
    no_jpg = 0
    for fn, lat, lng, city, dsrc in rows:
        if not fn.lower().endswith(('.jpg', '.jpeg')):
            no_jpg += 1
            continue
        fp = disk.get(fn.lower())
        if not fp:
            base = os.path.splitext(fn)[0].lower()
            for suf in ('_italia_2023', '_bosnia_2023'):
                fp = disk.get(base + suf + os.path.splitext(fn)[1].lower())
                if fp:
                    break
        if not fp:
            no_fisico += 1
            continue
        lat4, lng4 = round(lat, 4), round(lng, 4)
        key = (lat4, lng4, (city or 'Italy'))
        pendientes.setdefault(key, []).append(fp)

    total_target = sum(len(v) for v in pendientes.values())
    print('Clusters: {} | JPG a tratar: {} | no-jpg: {} | sin fisico: {}'.format(
        len(pendientes), total_target, no_jpg, no_fisico))

    # Bulk check: cuales YA tienen GPS
    all_files = [fp for v in pendientes.values() for fp in v]
    print('Comprobando GPS existente (llamada unica)...', flush=True)
    ya_gps = bulk_check_gps(all_files)
    print('Ya con GPS: {}'.format(len(ya_gps)))

    actualizados, omitidos, fallidos = 0, 0, []
    n_cluster = 0
    for (lat4, lng4, city), fpaths in sorted(pendientes.items()):
        n_cluster += 1
        todo = [f for f in fpaths if os.path.normcase(f) not in ya_gps]
        skip = len(fpaths) - len(todo)
        omitidos += skip
        if not todo:
            continue
        h3_idx = h3.latlng_to_cell(lat4, lng4, 9)
        ok, fail = write_group(todo, lat4, lng4, city, h3_idx)
        actualizados += ok
        fallidos.extend(fail)
        print('[{}/{}] {} {} -> {} ok, {} fail'.format(
            n_cluster, len(pendientes), city, (lat4, lng4), ok, len(fail)),
            flush=True)

    # Reintento de fallidos con delay mayor
    if fallidos:
        print('\nReintentando {} fallidos...'.format(len(fallidos)))
        time.sleep(1)
        retry = [f for f in fallidos if os.path.normcase(f) not in
                 bulk_check_gps(fallidos)]
        if retry:
            for f in retry:
                # reintento individual
                pass  # se reintenta abajo por cluster
        # reintento simple: una llamada mas agrupando por coord
        by_coord = {}
        for f in fallidos:
            # buscar cluster
            for (la, ln, ci), lst in pendientes.items():
                if f in lst:
                    by_coord.setdefault((la, ln, ci), []).append(f)
                    break
        for (la, ln, ci), lst in by_coord.items():
            h3_idx = h3.latlng_to_cell(la, ln, 9)
            ok, fail = write_group(lst, la, ln, ci, h3_idx)
            actualizados += ok
            fallidos = fail
            if ok:
                print('  retry {} -> {}'.format(ci, ok))

    print('\n=== RESUMEN ===')
    print('Actualizados: {}'.format(actualizados))
    print('Omitidos (ya tenian GPS): {}'.format(omitidos))
    print('Fallidos: {}'.format(len(fallidos)))
    if fallidos:
        for f in fallidos[:10]:
            print('  {}'.format(os.path.basename(f)))

    # Verificacion masiva
    print('\n=== VERIFICACION (muestra) ===')
    sample = all_files[:3] + all_files[-3:]
    have = bulk_check_gps(sample)
    for f in sample:
        print('  {} -> {}'.format(os.path.basename(f),
              'OK' if os.path.normcase(f) in have else 'SIN GPS'))


if __name__ == '__main__':
    main()
