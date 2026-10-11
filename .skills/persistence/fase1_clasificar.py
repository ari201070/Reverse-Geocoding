#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, shutil, hashlib, sqlite3, re, io
from pathlib import Path
from datetime import datetime
from collections import defaultdict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DRY_RUN = "--execute" not in sys.argv
ROOT = Path("F:/")
DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
MONTH_NAMES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
MEDIA_EXTS = {".jpg",".jpeg",".png",".heic",".heif",".webp",".tiff",".tif",".bmp",".gif",".raw",".cr2",".nef",".arw",".dng",".mp4",".mov",".avi",".mkv",".3gp",".wmv"}
PROTECTED = ["F:/copia de los datos de Google"]

def fhash(p):
    h = hashlib.sha256()
    try:
        with open(p,"rb") as f:
            while True:
                c = f.read(65536)
                if not c: break
                h.update(c)
        return h.hexdigest()
    except: return None

def classify_by_mtime(fp):
    try:
        dt = datetime.fromtimestamp(os.path.getmtime(fp))
        if 2000<=dt.year<=2030 and 1<=dt.month<=12:
            return dt.year, f"{dt.month:02d}-{MONTH_NAMES[dt.month-1]}"
    except: pass
    return None, None

def get_best(paths):
    best, bs = None, -1
    for p in paths:
        try:
            s = p.stat().st_size
            if s > bs: bs, best = s, p
        except: pass
    return best or paths[0]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    conn.execute("DROP TABLE IF EXISTS photos")
    conn.execute("""CREATE TABLE photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_path TEXT, final_path TEXT, filename TEXT,
        file_hash TEXT, file_size INTEGER, date_taken TEXT,
        year INTEGER, month_folder TEXT,
        lat REAL, lng REAL, location_name TEXT,
        is_duplicate INTEGER DEFAULT 0, merged_from TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    return conn

def main():
    mode = "[DRY RUN]" if DRY_RUN else "[EJECUCION REAL]"
    print(f"\n{'='*60}")
    print(f"  {mode} Clasificacion + Deduplicacion + DB")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    print("\n  [1/5] Escaneando archivos multimedia...")
    all_files = []
    for item in sorted(ROOT.iterdir()):
        if not item.is_dir(): continue
        n = item.name
        if not (n.isdigit() and len(n)==4 and 2000<=int(n)<=2030): continue
        for root, dirs, files in os.walk(str(item)):
            rp = Path(root)
            rel = rp.relative_to(item)
            if rel.parts and re.match(r"\d{2}-\w+", rel.parts[0]): continue
            if any(".Papelera" in p for p in rel.parts): continue
            for f in files:
                fp = rp / f
                if fp.suffix.lower() in MEDIA_EXTS:
                    all_files.append(fp)
    print(f"      {len(all_files)} archivos encontrados")

    print("\n  [2/5] Clasificando por mtime...")
    classified, unclassified = [], []
    for fp in all_files:
        y, mf = classify_by_mtime(fp)
        if y and mf:
            classified.append((fp, y, mf))
        else:
            unclassified.append(fp)
    print(f"      {len(classified)} clasificados, {len(unclassified)} sin fecha")

    print("\n  [3/5] Agrupando duplicados...")
    groups = defaultdict(list)
    for fp, y, mf in classified:
        base = fp.stem
        base = re.sub(r"^(Screenshot_|IMG-|VID-|IMG_|VID_|DSCN?_?)", "", base)
        ts = re.search(r"(\d{4}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2})", base)
        key = re.sub(r"[-_\s]","",ts.group(1)) if ts else base.lower().strip()
        groups[key].append((fp, y, mf))

    total_groups = len(groups)
    dup_groups = len([g for g in groups.values() if len(g)>1])
    print(f"      {total_groups} grupos, {dup_groups} con duplicados")

    print("\n  [4/5] Moviendo y descartando...")
    conn = init_db() if not DRY_RUN else None
    moved, trashed, skipped, errors = 0, 0, 0, 0
    processed = 0
    batch = []

    for key, members in groups.items():
        processed += 1
        if processed % 2000 == 0:
            print(f"      ...{processed}/{total_groups} ({moved} movidos, {trashed} descartados)")

        if len(members) == 1:
            fp, y, mf = members[0]
            dest_dir = ROOT / str(y) / mf
            dest_file = dest_dir / fp.name
            if not DRY_RUN:
                try:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    if dest_file.exists():
                        os.remove(str(fp)); skipped += 1; continue
                    shutil.move(str(fp), str(dest_file))
                except: errors += 1; continue
            moved += 1
            if conn:
                batch.append((str(fp), str(dest_file), fp.name, None, fp.stat().st_size if fp.exists() else 0, None, y, mf, 0, None))
            continue

        paths = [m[0] for m in members]
        best = get_best(paths)
        best_y = next(m[1] for m in members if m[0]==best)
        best_mf = next(m[2] for m in members if m[0]==best)
        dest_dir = ROOT / str(best_y) / best_mf
        dest_file = dest_dir / best.name

        if not DRY_RUN:
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                if dest_file.exists(): os.remove(str(best))
                else: shutil.move(str(best), str(dest_file))
            except: errors += 1; continue

        trash_ids = []
        for fp2, y2, mf2 in members:
            if fp2 == best: continue
            trash_dir = ROOT / f".Papelera_Deduplicacion{best_y}" / best_mf
            if not DRY_RUN:
                try:
                    trash_dir.mkdir(parents=True, exist_ok=True)
                    td = trash_dir / fp2.name
                    if td.exists(): os.remove(str(fp2)); skipped += 1
                    else: shutil.move(str(fp2), str(td)); trashed += 1
                    trash_ids.append(str(fp2))
                except:
                    try: os.remove(str(fp2))
                    except: pass
                    errors += 1
            else: trashed += 1

        moved += 1
        if conn:
            sz = dest_file.stat().st_size if dest_file.exists() else 0
            batch.append((str(best), str(dest_file), best.name, None, sz, None, best_y, best_mf, 0, ",".join(trash_ids) if trash_ids else None))

        if len(batch) >= 1000 and conn:
            conn.executemany("INSERT INTO photos (original_path,final_path,filename,file_hash,file_size,date_taken,year,month_folder,is_duplicate,merged_from) VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
            conn.commit(); batch = []

    if conn and batch:
        conn.executemany("INSERT INTO photos (original_path,final_path,filename,file_hash,file_size,date_taken,year,month_folder,is_duplicate,merged_from) VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
        conn.commit()

    print("\n  [5/5] Reporte final...")
    if conn:
        total_db = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        unique_db = conn.execute("SELECT COUNT(DISTINCT final_path) FROM photos").fetchone()[0]
        years_db = conn.execute("SELECT COUNT(DISTINCT year) FROM photos").fetchone()[0]
        months_db = conn.execute("SELECT COUNT(DISTINCT month_folder) FROM photos").fetchone()[0]
        conn.close()
    else:
        total_db = unique_db = years_db = months_db = 0

    print(f"\n{'='*60}")
    print(f"  RESUMEN {'DRY RUN' if DRY_RUN else 'EJECUTADO'}")
    print(f"{'='*60}")
    print(f"  Archivos escaneados:     {len(all_files)}")
    print(f"  Clasificados:            {len(classified)}")
    print(f"  Sin fecha:               {len(unclassified)}")
    print(f"  Unicos movidos:          {moved}")
    print(f"  Duplicados descartados:  {trashed}")
    print(f"  Ya existentes (hash):    {skipped}")
    print(f"  Errores:                 {errors}")
    if conn:
        print(f"  --- photo_catalog.db ---")
        print(f"  Registros:               {total_db}")
        print(f"  Fotos unicas en disco:   {unique_db}")
        print(f"  Anios:                   {years_db}")
        print(f"  Carpetas de mes:         {months_db}")
    if DRY_RUN: print(f"\n  [!] Re-ejecuta con --execute")
    else: print(f"\n  [OK] Disco + DB actualizados")

if __name__ == "__main__":
    main()
