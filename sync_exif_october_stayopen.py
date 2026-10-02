#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizacion EXIF Octubre 2023 - stay_open (un solo proceso exiftool)
Escribe GPS + ImageDescription (city) + UserComment (H3) en JPG fisicos.
Evita 0xC0000142/timeouts por spawning masivo de procesos.
"""
import os
import json
import time
import sqlite3
import subprocess
import h3

ROOT = r'F:\2023\10-Octubre'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'photo_catalog.db')
EXIFTOOL = r'C:\Users\flier\AppData\Local\Programs\ExifTool\exiftool.exe'


class ExifSession:
    def __init__(self):
        self.proc = subprocess.Popen(
            [EXIFTOOL, '-stay_open', 'True', '-@', '-'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding='utf-8',
            errors='replace', bufsize=1)

    def run(self, args, timeout=60):
        cmd = '\n'.join(args) + '\n-execute\n'
        self.proc.stdin.write(cmd)
        self.proc.stdin.flush()
        out_lines = []
        err_lines = []
        start = time.time()
        while True:
            if time.time() - start > timeout:
                raise TimeoutError('exiftool stay_open timeout')
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError('exiftool pipe closed: ' +
                                   self.proc.stderr.read())
            if line.strip() == '{ready}':
                break
            out_lines.append(line.rstrip('\n'))
        # stderr no bloqueante: exiftool reporta warnings ahi; lo drenamos
        # (solo disponible si el proceso escribio algo; no bloqueamos)
        return '\n'.join(out_lines)

    def close(self):
        try:
            self.proc.stdin.write('-stay_open\nFalse\n-execute\n')
            self.proc.stdin.flush()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

    def restart(self):
        try:
            self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            pass
        self.__init__()


def write_group(sess, files, lat, lng, city, h3_idx, place=None, url=None):
    ref_lat = 'N' if lat >= 0 else 'S'
    ref_lng = 'E' if lng >= 0 else 'W'
    label = place or city
    user_comment = 'Motor Refactorizado v2.0 | H3: {} | {}'.format(
        h3_idx,
        json.dumps({"place": label, "evento": "viaje_italia_2023",
                    "metodo": "VOUCHER_STRICT"},
                   ensure_ascii=False))
    
    # Base URL opcional
    base_url_arg = []
    if url:
        base_url_arg = ['-XMP-xmp:BaseURL=' + url]
    
    ok, fail = 0, []
    for i in range(0, len(files), 8):
        part = files[i:i + 8]
        args = ['-m', '-overwrite_original',
                '-GPSLatitude={:.4f}'.format(abs(lat)),
                '-GPSLatitudeRef=' + ref_lat,
                '-GPSLongitude={:.4f}'.format(abs(lng)),
                '-GPSLongitudeRef=' + ref_lng,
                '-GPSVersionID=2 3 0 0',
                '-ImageDescription=' + label,
                '-UserComment=' + user_comment] + base_url_arg + part
        try:
            out = sess.run(args, timeout=60)
            # ... (rest of function)

        try:
            out = sess.run(args, timeout=60)
            if 'updated' in out.lower() and "weren't" not in out.lower():
                ok += len(part)
            elif 'were' in out and "weren't" not in out.lower():
                ok += len(part)
            else:
                # cuenta individual
                n_ok = sum(1 for l in out.splitlines()
                           if 'updated' in l.lower() and
                           "weren't" not in l.lower())
                # fallback: si hay cualquier 'updated' sin negacion, asume ok
                if 'files updated' in out.lower() and "weren't" not in out.lower():
                    ok += len(part)
                else:
                    fail.extend(part)
        except Exception as e:
            print('  EXC chunk ({} files): {}'.format(len(part), e))
            if 'timeout' in str(e).lower():
                sess.restart()
                print('    sesion reiniciada')
            # reintento archivo por archivo dentro del chunk
            for f in part:
                single = args[:len(args) - len(part)] + [f]
                try:
                    out = sess.run(single, timeout=45)
                    if 'updated' in out.lower() and "weren't" not in out.lower():
                        ok += 1
                    else:
                        fail.append(f)
                except Exception as e2:
                    print('    EXC file {}: {}'.format(os.path.basename(f), e2))
                    fail.append(f)
                time.sleep(0.1)
        time.sleep(0.15)
    return ok, fail


def bulk_have_gps(sess, files, chunk=150):
    have = set()
    for i in range(0, len(files), chunk):
        part = files[i:i + chunk]
        out = sess.run(['-m', '-j', '-GPSLatitude', '-UserComment'] + part,
                       timeout=120)
        if out.strip():
            try:
                for item in json.loads(out):
                    if ('GPSLatitude' in item and
                            'H3' in str(item.get('UserComment', ''))):
                        have.add(os.path.normcase(item['SourceFile']))
            except json.JSONDecodeError:
                pass
    return have


def main():
    con = sqlite3.connect(DB_PATH, timeout=30)
    cur = con.cursor()
    cur.execute('''
        SELECT filename, latitude, longitude, city, location_name,
               h3_index, location_source, voucher_url
        FROM photos
        WHERE date_taken LIKE '2023-10-%'
          AND latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY date_taken
    ''')
    rows = cur.fetchall()
    con.close()
    print('Registros DB con GPS (Oct 2023): {}'.format(len(rows)))

    disk = {}
    for f in os.listdir(ROOT):
        if f.lower().endswith(('.jpg', '.jpeg')):
            disk[f.lower()] = os.path.join(ROOT, f)
    print('Fisicos .jpg/.jpeg: {}'.format(len(disk)))

    clusters = {}
    force = set()
    no_fisico = no_jpg = 0
    for fn, lat, lng, city, loc_name, h3_db, src, vurl in rows:
        if not fn.lower().endswith(('.jpg', '.jpeg')):
            no_jpg += 1
            continue
        fp = disk.get(fn.lower())
        if not fp:
            base, ext = os.path.splitext(fn)
            fp = disk.get((base + '_Italia_2023' + ext).lower())
            if not fp:
                fp = disk.get((base + '_Bosnia_2023' + ext).lower())
        if not fp:
            no_fisico += 1
            continue
        place = loc_name or city or 'Italy'
        key = (round(lat, 4), round(lng, 4), city or 'Italy', place,
               h3_db, vurl)
        clusters.setdefault(key, []).append(fp)
        if src == 'VOUCHER_STRICT':
            force.add(os.path.normcase(fp))

    total = sum(len(v) for v in clusters.values())
    print('Clusters: {} | JPG: {} | no-jpg: {} | sin fisico: {} | forzados: {}'.format(
        len(clusters), total, no_jpg, no_fisico, len(force)))

    import sys
    only_forced = '--only-forced' in sys.argv
    sess = ExifSession()
    try:
        all_files = [f for v in clusters.values() for f in v]
        if only_forced:
            forced_files = [f for v in clusters.values() for f in v
                            if os.path.normcase(f) in force]
            print('Verificando {} forzados ya escritos...'.format(
                len(forced_files)), flush=True)
            done = set()
            for i in range(0, len(forced_files), 150):
                part = forced_files[i:i + 150]
                try:
                    out = sess.run(['-m', '-T', '-filename',
                                    '-UserComment'] + part, timeout=120)
                    for line in out.splitlines():
                        if 'VOUCHER_STRICT' in line:
                            done.add(line.split('\t')[0].lower())
                except Exception as e:
                    print('  aviso verificacion: {}'.format(e))
            have = set()
            for v in clusters.values():
                for f in v:
                    if (os.path.basename(f).lower() in done
                            and os.path.normcase(f) in force):
                        have.add(os.path.normcase(f))
            print('Forzados ya correctos: {} | pendientes: {}'.format(
                len(have), len(forced_files) - len(have)), flush=True)
        else:
            print('Bulk check GPS...', flush=True)
            have = bulk_have_gps(sess, all_files)
            print('Ya con GPS: {}'.format(len(have)))

        actualizados = omitidos = 0
        fallidos = []
        for n, ((lat, lng, city, place, h3_db, vurl), fpaths) in enumerate(
                sorted(clusters.items()), 1):
            todo = [f for f in fpaths
                    if os.path.normcase(f) not in have
                    or os.path.normcase(f) in force]
            if only_forced:
                todo = [f for f in fpaths
                        if os.path.normcase(f) in force]
            omitidos += len(fpaths) - len(todo)
            if not todo:
                continue
            h3_idx = h3_db or h3.latlng_to_cell(lat, lng, 9)
            ok, fail = write_group(sess, todo, lat, lng, city, h3_idx,
                                   place, url=vurl)
            actualizados += ok
            fallidos.extend(fail)
            print('[{}/{}] {} {} -> {} ok, {} fail'.format(
                n, len(clusters), place[:40], (lat, lng), ok,
                len(fail)),
                flush=True)

        if fallidos:
            print('\nReintentando {} fallidos...'.format(len(fallidos)))
            time.sleep(2)
            by_c = {}
            for f in fallidos:
                for (la, ln, ci, pl, hdb, vu), lst in clusters.items():
                    if f in lst:
                        by_c.setdefault((la, ln, ci, pl, hdb, vu), []).append(f)
                        break
            retry_fail = []
            for (la, ln, ci, pl, hdb, vu), lst in by_c.items():
                h3_idx = hdb or h3.latlng_to_cell(la, ln, 9)
                ok, fail = write_group(sess, lst, la, ln, ci, h3_idx, pl, url=vu)
                actualizados += ok
                retry_fail.extend(fail)
                print('  retry {} -> {} ok, {} fail'.format(pl[:40], ok,
                      len(fail)))
            fallidos = retry_fail

        print('\n=== RESUMEN ===')
        print('Actualizados: {}'.format(actualizados))
        print('Omitidos (ya GPS): {}'.format(omitidos))
        print('Fallidos: {}'.format(len(fallidos)))
        for f in fallidos[:10]:
            print('  ', os.path.basename(f))

        print('\n=== VERIFICACION ===')
        sample = all_files[::max(1, len(all_files) // 8)][:8]
        h2 = bulk_have_gps(sess, sample)
        for f in sample:
            print('  {} -> {}'.format(os.path.basename(f),
                  'OK' if os.path.normcase(f) in h2 else 'SIN GPS'))
    finally:
        sess.close()


if __name__ == '__main__':
    main()