# -*- coding: utf-8 -*-
import os, sys, io, sqlite3, shutil, re
from pathlib import Path
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
IMAGE_EXTS = {".jpg",".jpeg",".png",".tiff",".tif",".bmp",".gif",".webp",".heic",".heif"}
VIDEO_EXTS = {".mp4",".mov",".avi",".mkv",".wmv",".m4v",".3gp",".webm"}
ALL_MEDIA = IMAGE_EXTS | VIDEO_EXTS
HIDDEN_FILES = {"Thumbs.db","desktop.ini",".DS_Store","ehthumbs.db"}

def get_exif_date(fp):
    try:
        import piexif
        d = piexif.load(str(fp))
        dt = d.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
        if dt: return dt.decode("utf-8").strip()
    except: pass
    try:
        from PIL import Image
        img = Image.open(str(fp))
        exif = img._getexif()
        if exif:
            from PIL.ExifTags import TAGS
            for tid, v in exif.items():
                if TAGS.get(tid) == "DateTimeOriginal" and v: return v.strip()
    except: pass
    return None

def is_media(f): return Path(f).suffix.lower() in ALL_MEDIA
def is_hidden(f): return f in HIDDEN_FILES or f.startswith("._") or f.startswith(".")

def main():
    sep = "=" * 65
    print()
    print(sep)
    print("  REPARACION Y LIMPIEZA - DISCO F:")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(sep)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    c = conn.cursor()
    # FASE 1
    print()
    print("  [FASE 1] Reparacion de F:/2009/11-Noviembre")
    nov_dir = Path("F:/2009/11-Noviembre")
    ago_dir = Path("F:/2009/08-Agosto")
    moved_count = 0; no_exif = 0; skipped_cf = 0
    if not nov_dir.exists():
        print("    Carpeta NO existe. Saltando.")
    else:
        files = [f for f in nov_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
        print("    Archivos: " + str(len(files)))
        for fp in files:
            exif_dt = get_exif_date(fp)
            if not exif_dt: no_exif += 1; continue
            try: dt = datetime.strptime(exif_dt, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                try: dt = datetime.strptime(exif_dt, "%Y-%m-%d %H:%M:%S")
                except ValueError: no_exif += 1; continue
            if dt.month == 8:
                if not ago_dir.exists(): ago_dir.mkdir(parents=True, exist_ok=True); print("    Creada: F:/2009/08-Agosto/")
                dest = ago_dir / fp.name
                if dest.exists(): print("    CONFLICTO: " + fp.name); skipped_cf += 1; continue
                shutil.move(str(fp), str(dest))
                moved_count += 1
                print("    MOVIDO: " + fp.name + " -> 08-Agosto/")
                old_p = str(fp).replace(os.sep, "/")
                new_p = str(dest).replace(os.sep, "/")
                c.execute("UPDATE photos SET final_path=?, month_folder='08-Agosto' WHERE final_path=?", (new_p, old_p))
                c.execute("UPDATE photos SET final_path=?, month_folder='08-Agosto' WHERE original_path=?", (new_p, old_p))
        conn.commit()
        print()
        print("    --- FASE 1 RESULTADO ---")
        print("    Movidos Nov->Ago:  " + str(moved_count))
        print("    Sin EXIF:          " + str(no_exif))
        print("    Conflictos:        " + str(skipped_cf))
    # FASE 2
    print()
    print("  [FASE 2] Limpieza de carpetas mensuales viejas vacias")
    OLD = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
           "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre",
           "enero","febrero","marzo","abril","mayo","junio",
           "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    deleted = []; protected = []; errors = []
    for year in range(2005, 2027):
        yd = Path("F:/" + str(year))
        if not yd.exists(): continue
        for item in yd.iterdir():
            if not item.is_dir() or item.name.startswith("."): continue
            if item.name not in OLD: continue
            media = [f for f in item.rglob("*") if f.is_file() and is_media(f.name)]
            hiddens = [f for f in item.rglob("*") if f.is_file() and is_hidden(f.name)]
            if len(media) > 0: protected.append(str(item)); continue
            for hf in hiddens:
                try: hf.unlink()
                except: pass
            try: item.rmdir(); deleted.append(str(item))
            except OSError as e: errors.append((str(item), str(e)))
    conn.close()
    print()
    print("  --- FASE 2 RESULTADO ---")
    print("  Carpetas viejas eliminadas: " + str(len(deleted)))
    for d in deleted: print("    - " + d)
    if protected:
        print()
        print("  Carpetas viejas CON fotos (protegidas): " + str(len(protected)))
        for p in protected: print("    - " + p)
    if errors:
        print()
        print("  Errores: " + str(len(errors)))
        for s, e in errors: print("    - " + s + ": " + e)
    # FASE 3
    print()
    print("  [FASE 3] Verificacion de carpetas sobrevivientes")
    surviving = []
    for year in range(2005, 2027):
        yd = Path("F:/" + str(year))
        if not yd.exists(): continue
        for item in yd.iterdir():
            if not item.is_dir() or item.name.startswith("."): continue
            if item.name in OLD: surviving.append(str(item))
    if surviving:
        print("  ALERTA: " + str(len(surviving)) + " carpetas viejas aun existen:")
        for s in surviving: print("    - " + s)
    else:
        print("  OK: No quedan carpetas viejas sin formato MM- en F:")
    print()
    print(sep)
    print("  RESUMEN FINAL")
    print(sep)
    print("  Fotos 2009 movidas Nov->Ago: " + str(moved_count))
    print("  Carpetas viejas eliminadas:  " + str(len(deleted)))
    print("  Carpetas viejas protegidas:  " + str(len(protected)))
    print("  Errores de borrado:          " + str(len(errors)))
    print(sep)

if __name__ == "__main__":
    main()
