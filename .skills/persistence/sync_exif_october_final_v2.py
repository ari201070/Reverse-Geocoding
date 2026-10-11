#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronización física EXIF para el lote de Octubre 2023 - Solo JPG sin GPS
Escribe coordenadas, place_name, tags y H3 en los archivos físicos
"""
import os
import re
import sqlite3
import subprocess
import json
import h3
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

ROOT = r'F:\2023\10-Octubre'
DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
EXIFTOOL = r'C:\Users\flier\AppData\Local\Programs\ExifTool\exiftool.exe'

def has_gps(fp):
    """Check if file already has GPS data"""
    try:
        r = subprocess.run([EXIFTOOL, '-m', '-GPSLatitude', fp], capture_output=True, text=True, timeout=15)
        return 'GPS Latitude' in r.stdout and ':' in r.stdout
    except:
        return False

def main():
    con = sqlite3.connect('data/photo_catalog.db', timeout=30)
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cur = con.cursor()
    cur.execute('''
        SELECT id, filename, latitude, longitude, place_name, h3_index, tags, date_taken, location_time
        FROM photos 
        WHERE date_taken LIKE "2023-10-%" 
        AND latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY date_taken
    ''')
    rows = cur.fetchall()
    print("Registros con GPS en DB para Oct 2023: {}".format(len(rows)))

    actualizados = 0
    errores = 0
    omitidos = 0
    ya_tienen_gps = 0

    for pid, filename, latitude, longitude, place_name, h3_idx, tags, date_taken, loc_time in con.execute('''
        SELECT id, filename, latitude, longitude, place_name, h3_index, tags, date_taken, location_time
        FROM photos 
        WHERE date_taken LIKE "2023-10-%" 
        AND latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY date_taken
    ''').fetchall():
        fn = filename
        lat, lng = latitude, longitude
        if lat is None or lng is None:
            continue

        # Solo procesar JPG/JPEG, omitir mp4
        if not fn.lower().endswith(('.jpg', '.jpeg')):
            omitidos += 1
            continue

        fp = os.path.join(r'F:\2023\10-Octubre', filename)
        if not os.path.exists(fp):
            for f in os.listdir(r'F:\2023\10-Octubre'):
                if f.lower() == filename.lower():
                    fp = os.path.join(r'F:\2023\10-Octubre', f)
                    break

        if not os.path.exists(fp):
            continue

        # Skip if already has GPS
        if has_gps(fp):
            ya_tienen_gps += 1
            continue

        lat = round(latitude, 4)
        lng = round(longitude, 4)
        h3_idx = h3.latlng_to_cell(lat, lng, 9) if lat and lng else None

        dt_str = date_taken
        dt_fmt = date_taken.replace('-', ':').replace('  ', ' ')
        if ' ' in dt_str and ':' not in dt_str.split(' ')[-1]:
            dt_str = dt_str + ':00'
        m = re.match(r'(\d{4})[:\-](\d{2})[:\-](\d{2})[ T](\d{2}):(\d{2}):(\d{2})', dt_str)
        if m:
            y, mo, da, hh, mm, ss = m.groups()
            dt_fmt = '{}:{}:{} {}:{}:{}'.format(y, mo, da, hh, mm, ss)
        else:
            dt_fmt = dt_str.replace('-', ':')

        cmd = [
            EXIFTOOL,
            '-m',  # Ignore minor errors/warnings
            '-overwrite_original',
            '-GPSLatitude={:.4f}'.format(abs(lat)),
            '-GPSLatitudeRef={}'.format('N' if lat >= 0 else 'S'),
            '-GPSLongitude={:.4f}'.format(abs(lng)),
            '-GPSLongitudeRef={}'.format('E' if lng >= 0 else 'W'),
            '-GPSVersionID=2 3 0 0',
            '-ImageDescription=Roma',
            '-UserComment=Motor Refactorizado v1.0 | H3: {} | {}'.format(h3_idx, json.dumps({"place": "Roma", "evento": "viaje_italia_2023"}, ensure_ascii=False)[:100]),
            '-DateTimeOriginal=' + dt_fmt,
            '-CreateDate=' + dt_fmt,
            fp
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 or 'updated' in result.stdout.lower():
                actualizados += 1
            else:
                errores += 1
                print('Error {}: rc={} stderr={}'.format(filename, result.returncode, result.stderr[:100]))
        except Exception as e:
            print('Error {}: {}'.format(fn, e))
            errores += 1
        
        time.sleep(0.05)

    print('Actualizados: {}'.format(actualizados))
    print('Errores: {}'.format(errores))
    print('Omitidos (no JPG): {}'.format(omitidos))
    print('Ya tenian GPS: {}'.format(ya_tienen_gps))

    # Verificación
    print('\n=== VERIFICACION POST-ESCRITURA ===')
    for fn in ['2023-10-02 09.00.58.jpg', '2023-10-02 11.28.01.jpg', '2023-10-02 14.54.11.jpg']:
        fp = os.path.join(r'F:\2023\10-Octubre', fn)
        if os.path.exists(fp):
            r = subprocess.run([EXIFTOOL, '-m', '-GPSLatitude', '-GPSLongitude', '-ImageDescription', '-UserComment', os.path.join(r'F:\2023\10-Octubre', fn)], capture_output=True, text=True, timeout=15)
            print(fn + ':')
            print(r.stdout[:300])

if __name__ == '__main__':
    main()
