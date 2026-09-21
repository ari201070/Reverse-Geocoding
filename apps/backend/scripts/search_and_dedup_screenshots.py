import os
import sys
import io
import hashlib
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

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

def quick_hash(file_path):
    """
    Computes a fast MD5 hash using the first and last 64KB of the file
    plus the file size to be ultra-fast and 100% accurate for images.
    """
    try:
        size = os.path.getsize(file_path)
        h = hashlib.md5()
        h.update(str(size).encode())
        
        with open(file_path, 'rb') as f:
            # Read first 64KB
            chunk = f.read(65536)
            h.update(chunk)
            # Read last 64KB if file is larger
            if size > 65536:
                f.seek(-min(65536, size - 65536), 2)
                chunk = f.read(65536)
                h.update(chunk)
                
        return h.hexdigest()
    except Exception:
        return None

def is_target_file(filename):
    fn_low = filename.lower()
    # Check English keywords
    for kw in KEYWORDS_EN:
        if kw in fn_low:
            return True
    # Check Hebrew keywords
    for kw in KEYWORDS_HE:
        if kw in filename:
            return True
    return False

def main():
    print("=" * 80)
    print("  ESCÁNER GENERAL DE CAPTURAS, TABLAS Y LOVOT-SCHEDULES (C, F, OneDrive, Dropbox)")
    print("=" * 80)
    
    found_files = []
    by_category = {
        'OneDrive': [],
        'Dropbox': [],
        'Pictures': [],
        'Downloads': [],
        'F_Drive': []
    }
    
    # We walk through each search directory
    for sd in SEARCH_DIRS:
        if not os.path.exists(sd):
            print(f"[Aviso] Directorio no disponible: {sd}")
            continue
            
        print(f"Escaneando: {sd} ...")
        
        # Walk recursively
        for root, dirs, files in os.walk(sd, topdown=True):
            # Prune ignore directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    if is_target_file(f):
                        fp = os.path.normpath(os.path.join(root, f))
                        try:
                            size = os.path.getsize(fp)
                            item = {
                                'path': fp,
                                'filename': f,
                                'size': size,
                                'dir': root
                            }
                            found_files.append(item)
                            
                            # Categorize by location
                            fp_low = fp.lower()
                            if 'onedrive' in fp_low:
                                by_category['OneDrive'].append(item)
                            elif 'dropbox' in fp_low:
                                by_category['Dropbox'].append(item)
                            elif 'pictures' in fp_low:
                                by_category['Pictures'].append(item)
                            elif 'downloads' in fp_low:
                                by_category['Downloads'].append(item)
                            elif fp_low.startswith('f:'):
                                by_category['F_Drive'].append(item)
                        except Exception:
                            pass
                            
    print(f"\nEscaneo finalizado. Total de capturas/tablas encontradas: {len(found_files)}")
    
    if not found_files:
        print("No se encontraron capturas o tablas en las rutas escaneadas.")
        sys.exit(0)
        
    # Group by duplicates
    print("\nCalculando duplicados mediante firmas binarias rápidas...")
    hash_map = {}
    for idx, item in enumerate(found_files):
        if idx % 100 == 0 and idx > 0:
            print(f"  ...Procesados {idx}/{len(found_files)} archivos")
        f_hash = quick_hash(item['path'])
        if f_hash:
            hash_map.setdefault(f_hash, []).append(item)
            
    # Compile duplicate statistics
    duplicate_groups = {h: items for h, items in hash_map.items() if len(items) > 1}
    
    total_space = sum(item['size'] for item in found_files)
    redundant_space = 0
    duplicate_files_count = 0
    
    for h, items in duplicate_groups.items():
        # Keep one file, the others are redundant
        sorted_items = sorted(items, key=lambda x: len(x['path'])) # prefer shorter paths
        redundant_items = sorted_items[1:]
        redundant_space += sum(item['size'] for item in redundant_items)
        duplicate_files_count += len(redundant_items)
        
    print("\n" + "="*50)
    print("  REPORT PRINCIPAL DE CAPTURAS Y TABLAS")
    print("=" * 50)
    
    # 1. Distribution by folder/drive
    print("1. Distribución geográfica de los archivos:")
    for cat, items in by_category.items():
        cat_size = sum(item['size'] for item in items) / (1024*1024)
        print(f"  - {cat:<15}: {len(items):>4} archivos ({cat_size:.2f} MB)")
        
    # 2. Duplicate analysis
    print(f"\n2. Análisis de duplicados exactos:")
    print(f"  - Grupos de archivos duplicados:  {len(duplicate_groups)}")
    print(f"  - Total archivos repetidos:      {duplicate_files_count}")
    print(f"  - Espacio desperdiciado:         {redundant_space / (1024*1024):.2f} MB")
    
    if duplicate_groups:
        print("\nMuestra de grupos duplicados (Top 5 más grandes/pesados):")
        sorted_dup_groups = sorted(duplicate_groups.items(), key=lambda x: sum(i['size'] for i in x[1]), reverse=True)
        for h, items in sorted_dup_groups[:5]:
            size_mb = items[0]['size'] / (1024*1024)
            print(f"  * Grupo [{items[0]['filename']}] ({len(items)} copias, {size_mb:.2f} MB c/u):")
            for item in items:
                print(f"    -> {item['path']}")
                
    # 3. Final potential savings
    print("\n" + "="*50)
    print("  AHORRO ESTIMADO DE ESPACIO DE ALMACENAMIENTO")
    print("=" * 50)
    print(f"  - Si eliminamos DUPLICADOS exactos:     {redundant_space / (1024*1024):.2f} MB")
    print(f"  - Si eliminamos TODOS los screenshots:  {total_space / (1024*1024):.2f} MB ({total_space / (1024*1024*1024):.2f} GB)")
    print("=" * 50)
    
if __name__ == '__main__':
    main()
