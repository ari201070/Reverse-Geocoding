import os
import sys
import io
import sqlite3
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

SEARCH_DIRS = [
    'C:/Users/flier/OneDrive',
    'C:/Users/flier/Dropbox',
    'C:/Users/flier/Pictures',
    'C:/Users/flier/Downloads',
    'F:/'
]

IGNORE_DIRS = {
    'node_modules', '.git', 'AppData', '$RECYCLE.BIN', 'System Volume Information',
    'Program Files', 'Program Files (x86)', 'Windows', 'Local Settings', 'Temp'
}

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.heif')

# Target keywords in filenames
KEYWORDS_EN = ['screenshot', 'capture', 'excel', 'sheet', 'table', 'schedule', 'timetable', 'duty']
KEYWORDS_HE = ['לוח', 'תורנות', 'תורן', 'טבלה', 'סדר', 'מערכת', 'שבוע']

def is_target_file(filename):
    fn_low = filename.lower()
    for kw in KEYWORDS_EN:
        if kw in fn_low:
            return True
    for kw in KEYWORDS_HE:
        if kw in filename:
            return True
    return False

def main():
    print("=" * 80)
    print("  INICIANDO ELIMINACIÓN MASIVA DE CAPTURAS Y TABLAS (OPCIÓN B)")
    print("=" * 80)
    
    # 1. First, scan to find all files on disk
    found_files = []
    
    for sd in SEARCH_DIRS:
        if not os.path.exists(sd):
            continue
            
        print(f"Buscando en: {sd} ...")
        for root, dirs, files in os.walk(sd, topdown=True):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    if is_target_file(f):
                        fp = os.path.normpath(os.path.join(root, f))
                        try:
                            size = os.path.getsize(fp)
                            found_files.append({
                                'path': fp,
                                'filename': f,
                                'size': size
                            })
                        except Exception:
                            pass
                            
    total_files = len(found_files)
    print(f"\nSe encontraron {total_files} archivos físicos listos para eliminar.")
    
    if total_files == 0:
        print("No se encontraron archivos para eliminar.")
        sys.exit(0)
        
    # Connect to DB
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    
    deleted_physical = 0
    deleted_db = 0
    total_freed_bytes = 0
    
    try:
        conn.execute("BEGIN TRANSACTION;")
        
        for idx, item in enumerate(found_files):
            fp = item['path']
            size = item['size']
            fn = item['filename']
            
            # 1. Delete physical file
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                    deleted_physical += 1
                    total_freed_bytes += size
                except Exception as e:
                    print(f"  [Aviso] No se pudo eliminar el archivo {fp}: {e}")
                    continue
            else:
                # File already gone, but let's make sure it is cleared from DB anyway
                deleted_physical += 1
                total_freed_bytes += size
                
            # 2. Delete database record
            cursor = conn.execute("DELETE FROM photos WHERE filename = ? AND file_size = ?", (fn, size))
            deleted_db += cursor.rowcount
            
        conn.commit()
        
        print("\n" + "="*50)
        print("  PURGA COMPLETA REALIZADA CON ÉXITO")
        print("=" * 50)
        print(f"  - Archivos físicos eliminados:        {deleted_physical}/{total_files}")
        print(f"  - Registros de base de datos borrados: {deleted_db}")
        print(f"  - Espacio total de disco liberado:     {total_freed_bytes / (1024*1024):.2f} MB ({total_freed_bytes / (1024*1024*1024):.2f} GB)")
        print("=" * 50)
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR CRÍTICO] Falló el proceso de eliminación masiva: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
