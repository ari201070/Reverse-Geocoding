# -*- coding: utf-8 -*-
import os, sys, io, sqlite3, shutil
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

MIGRATIONS = [
    ("F:/2010/Junio", "F:/2010/06-Junio", "montenegro-2010"),
    ("F:/2013/Diciembre", "F:/2013/12-Diciembre", "mixed-december-2013"),
    ("F:/2015/Julio", "F:/2015/07-Julio", "slovenia-2015"),
    ("F:/2025/Octubre", "F:/2025/10-Octubre", "argentina-2025"),
]

def classify_italia_2023(filepath, conn):
    c = conn.cursor()
    fname = filepath.name
    row = c.execute("SELECT country, lat, lng FROM photos WHERE filename=?", (fname,)).fetchone()
    if not row:
        row = c.execute("SELECT country, lat, lng FROM photos WHERE final_path LIKE ?", ("%" + fname,)).fetchone()
    if row:
        country = row[0]
        if country and "Italia" in country:
            return "italia-2023"
        elif country and "Albania" in country:
            return "albania-2023"
    return "mixed-october-2023"

def run_migration(dry_run=True):
    mode = "DRY-RUN" if dry_run else "EJECUTANDO"
    print()
    print("=" * 60)
    print("  ESTANDARIZACION DE SOBREVIVIENTES - " + mode)
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    c = conn.cursor()
    total_moved = 0
    total_skipped = 0

    for src, dst, trip in MIGRATIONS:
        src_p = Path(src)
        dst_p = Path(dst)
        if not src_p.exists():
            print()
            print("  SKIP " + src + " (not exists)")
            continue
        print()
        print("  MIGRATE: " + src + " -> " + dst)
        print("  trip_name: " + trip)
        if not dry_run and not dst_p.exists():
            dst_p.mkdir(parents=True, exist_ok=True)
            print("    Creada: " + dst)
        files = [f for f in src_p.rglob("*") if f.is_file()]
        print("    Archivos: " + str(len(files)))
        for fp in files:
            dest = dst_p / fp.name
            if dest.exists():
                print("    SKIP (exists): " + fp.name)
                total_skipped += 1
                continue
            if not dry_run:
                shutil.move(str(fp), str(dest))
                old_p = str(fp).replace(os.sep, "/")
                new_p = str(dest).replace(os.sep, "/")
                c.execute("UPDATE photos SET final_path=?, trip_name=? WHERE final_path=?", (new_p, trip, old_p))
                c.execute("UPDATE photos SET final_path=?, trip_name=? WHERE original_path=?", (new_p, trip, old_p))
                print("    MOVED: " + fp.name)
            else:
                print("    WOULD MOVE: " + fp.name)
            total_moved += 1

    src_2023 = Path("F:/2023/Octubre")
    dst_2023 = Path("F:/2023/10-Octubre")
    if src_2023.exists():
        print()
        print("  MIGRATE: F:/2023/Octubre -> F:/2023/10-Octubre")
        print("  Clasificacion por pais via DB...")
        if not dry_run and not dst_2023.exists():
            dst_2023.mkdir(parents=True, exist_ok=True)
        files = [f for f in src_2023.rglob("*") if f.is_file()]
        print("    Archivos: " + str(len(files)))
        counts = {"italia-2023": 0, "albania-2023": 0, "mixed-october-2023": 0}
        for fp in files:
            trip = classify_italia_2023(fp, conn)
            counts[trip] = counts.get(trip, 0) + 1
            dest = dst_2023 / fp.name
            if not dry_run:
                if not dest.exists():
                    shutil.move(str(fp), str(dest))
                old_p = str(fp).replace(os.sep, "/")
                new_p = str(dest).replace(os.sep, "/")
                c.execute("UPDATE photos SET final_path=?, trip_name=? WHERE final_path=?", (new_p, trip, old_p))
                c.execute("UPDATE photos SET final_path=?, trip_name=? WHERE original_path=?", (new_p, trip, old_p))
                print("    MOVED [" + trip + "]: " + fp.name)
            else:
                print("    WOULD MOVE [" + trip + "]: " + fp.name)
            total_moved += 1
        print("    Clasificacion:")
        for t, cnt in counts.items():
            print("      " + t + ": " + str(cnt))

    if not dry_run:
        conn.commit()
    conn.close()

    if not dry_run:
        print()
        print("  Limpiando carpetas origen vacias...")
        for src, _, _ in MIGRATIONS:
            p = Path(src)
            if p.exists() and not any(p.iterdir()):
                p.rmdir()
                print("    ELIMINADA: " + src)
        p = Path("F:/2023/Octubre")
        if p.exists():
            for item in list(p.iterdir()):
                if item.is_dir() and not any(item.iterdir()):
                    item.rmdir()
                    print("    ELIMINADA: " + str(item))
            if not any(p.iterdir()):
                p.rmdir()
                print("    ELIMINADA: F:/2023/Octubre")

    print()
    print("=" * 60)
    print("  RESUMEN " + mode)
    print("=" * 60)
    print("  Archivos a mover:    " + str(total_moved))
    print("  Conflictos:          " + str(total_skipped))
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_migration(dry_run=args.dry_run)
    if args.dry_run:
        print()
        print("Ejecutando migracion real...")
        run_migration(dry_run=False)
