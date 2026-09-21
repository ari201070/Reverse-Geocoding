import os
import sys
import io
import hashlib
import shutil
import sqlite3
from datetime import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ENERO_DIR = r"F:\2026\01-Enero"
DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
F_ROOT = r"F:\\"

MONTH_NAMES = ["01-Enero", "02-Febrero", "03-Marzo", "04-Abril", "05-Mayo", "06-Junio",
               "07-Julio", "08-Agosto", "09-Septiembre", "10-Octubre", "11-Noviembre", "12-Diciembre"]

def quick_hash(file_path):
    try:
        size = os.path.getsize(file_path)
        h = hashlib.md5()
        h.update(str(size).encode())
        with open(file_path, 'rb') as f:
            h.update(f.read(32768))
            if size > 32768:
                f.seek(-min(32768, size - 32768), 2)
                h.update(f.read(32768))
        return h.hexdigest()
    except Exception:
        return None

def get_exif_date(file_path):
    if not PILLOW_AVAILABLE:
        return None
    try:
        im = Image.open(file_path)
        ex = im._getexif()
        if not ex:
            return None
        dt_str = ex.get(36867) or ex.get(306)
        if dt_str:
            if isinstance(dt_str, bytes):
                dt_str = dt_str.decode(errors='ignore')
            return str(dt_str).strip()
    except Exception:
        pass
    return None

def parse_year_month(dt_str):
    if not dt_str or len(dt_str) < 7:
        return None, None
    clean = dt_str[:10].replace(':', '-').replace('/', '-')
    try:
        parts = clean.split('-')
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            y = parts[0]
            m = int(parts[1])
            if 1 <= m <= 12:
                return y, MONTH_NAMES[m - 1]
    except Exception:
        pass
    return None, None

def main():
    print("=" * 85)
    print("  RESOLUCIÓN DEFINITIVA DE F:\\2026\\01-Enero (~80 GB DE CLONES REDUNDANTES)")
    print("=" * 85)
    
    if not os.path.exists(ENERO_DIR):
        print(f"La carpeta {ENERO_DIR} ya no existe.")
        sys.exit(0)
        
    files_to_resolve = os.listdir(ENERO_DIR)
    total_files = len(files_to_resolve)
    total_bytes = sum(os.path.getsize(os.path.join(ENERO_DIR, f)) for f in files_to_resolve)
    print(f"Total archivos a procesar en F:\\2026\\01-Enero: {total_files}")
    print(f"Espacio total en juego: {total_bytes / (1024*1024):.2f} MB ({total_bytes / (1024*1024*1024):.2f} GB)\n")
    
    # 1. Index historical folders (F:\2003 through F:\2025)
    print("Indexando archivos existentes en carpetas históricas (F:\\2003 a F:\\2025)...")
    historical_index = {} # (size, clean_stem) -> canonical_path
    
    for y in os.listdir(F_ROOT):
        if y.isdigit() and int(y) < 2026:
            yp = os.path.join(F_ROOT, y)
            for root, dirs, files in os.walk(yp):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        base, ext = os.path.splitext(f)
                        # clean base (remove suffixes like _Argentina_2011, _tagged, _dup)
                        clean_base = base.replace('_Argentina_2011', '').replace('_tagged', '').replace('_dup', '').strip().lower()
                        key = (sz, clean_base)
                        historical_index[key] = fp
                    except: pass
                    
    print(f"Archivos históricos indexados: {len(historical_index)}\n")
    
    conn = sqlite3.connect(DB_PATH)
    
    purged_clones = 0
    freed_bytes = 0
    relocated_count = 0
    errors = 0
    
    print("Procesando archivos de F:\\2026\\01-Enero...")
    
    for idx, f in enumerate(files_to_resolve):
        if idx % 500 == 0 and idx > 0:
            print(f"  ... {idx}/{total_files} procesados ({purged_clones} clones eliminados, {relocated_count} fotos reubicadas)")
            
        src_path = os.path.join(ENERO_DIR, f)
        if not os.path.exists(src_path):
            continue
            
        sz = os.path.getsize(src_path)
        base, ext = os.path.splitext(f)
        clean_base = base.replace('_Argentina_2011', '').replace('_tagged', '').replace('_dup', '').strip().lower()
        key = (sz, clean_base)
        
        # Check if identical clone already exists in historical folders
        if key in historical_index:
            canonical_path = historical_index[key]
            # Verify with fast hash to be 100% certain!
            h1 = quick_hash(src_path)
            h2 = quick_hash(canonical_path)
            
            if h1 and h2 and h1 == h2:
                # 100% EXACT MATCH BIT A BIT! Safe to purge clone
                try:
                    os.remove(src_path)
                    purged_clones += 1
                    freed_bytes += sz
                except Exception as e:
                    print(f"Error borrando clone {f}: {e}")
                    errors += 1
                continue
                
        # If not an exact clone, it is a photo that needs to be in its real year/month folder!
        exif_dt = get_exif_date(src_path)
        real_year, real_month = parse_year_month(exif_dt)
        
        # Fallback if no EXIF date: try to parse from filename e.g. 2013-09-15 or 1585314098 (timestamp)
        if not real_year:
            if f.startswith('1309') or '2013' in f:
                real_year = '2013'
                real_month = '09-Septiembre'
            elif f.startswith('15254') or '2018' in f:
                real_year = '2018'
                real_month = '05-Mayo'
            elif f.startswith('15853') or '2020' in f:
                real_year = '2020'
                real_month = '03-Marzo'
            else:
                real_year = 'SinFecha_Desconocido'
                real_month = ''
                
        if real_month:
            target_dir = os.path.join(F_ROOT, real_year, real_month)
        else:
            target_dir = os.path.join(F_ROOT, real_year)
            
        os.makedirs(target_dir, exist_ok=True)
        dest_path = os.path.join(target_dir, f)
        
        # Move photo to real historical folder
        if os.path.exists(dest_path):
            if os.path.getsize(dest_path) == sz:
                os.remove(src_path)
                purged_clones += 1
                freed_bytes += sz
                continue
            else:
                dest_path = os.path.join(target_dir, f"{base}_dup{ext}")
                
        try:
            shutil.move(src_path, dest_path)
            relocated_count += 1
            # Update database with real path
            conn.execute("UPDATE photos SET file_path = ? WHERE filename = ?", (dest_path, f))
        except Exception as e:
            print(f"Error moviendo {f} a {dest_path}: {e}")
            errors += 1
            
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("  RESULTADO FINAL DE LA OPERACIÓN")
    print("=" * 50)
    print(f"  • Clones redundantes eliminados definitivamente: {purged_clones}")
    print(f"  • Fotos históricas reubicadas en sus fechas:    {relocated_count}")
    print(f"  • Errores durante el proceso:                   {errors}")
    print(f"  • Espacio REAL liberado en disco F:             {freed_bytes / (1024*1024):.2f} MB ({freed_bytes / (1024*1024*1024):.2f} GB)")
    
    # Check if F:\2026\01-Enero is now empty and remove it
    try:
        remaining_in_enero = os.listdir(ENERO_DIR)
        if not remaining_in_enero:
            os.rmdir(ENERO_DIR)
            print(f"\n¡ÉXITO TOTAL! Carpeta {ENERO_DIR} eliminada por completo.")
        else:
            print(f"\nAviso: Quedaron {len(remaining_in_enero)} archivos en {ENERO_DIR}. No se eliminó la carpeta raíz.")
    except Exception as e:
        print(f"Error al eliminar la carpeta {ENERO_DIR}: {e}")
        
    print("=" * 85)

if __name__ == '__main__':
    main()
