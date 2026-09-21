import os
import sys
import io
import hashlib
import sqlite3

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

# Exact target files specified by the user
TARGET_FILES_ON_F = [
    r"F:\2024\01-Enero\IMG-20240108-WA0001.jpg",
    r"F:\2024\01-Enero\IMG-20240109-WA0000.jpg",
    r"F:\2024\05-Mayo\IMG-20240512-WA0003.jpg",
    r"F:\2024\05-Mayo\IMG-20240517-WA0000.jpg"
]

# Targeted search directories (highly optimized to prevent timeouts)
SEARCH_DIRS = [
    'C:/Users/flier/OneDrive',
    'C:/Users/flier/Dropbox',
    'C:/Users/flier/Pictures',
    'C:/Users/flier/Downloads',
    'F:/2024',
    'F:/2025',
    'F:/2026'
]

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.heif')

def get_fast_hash(p):
    if not os.path.exists(p):
        return None
    try:
        size = os.path.getsize(p)
        h = hashlib.md5()
        h.update(str(size).encode())
        with open(p, 'rb') as f:
            h.update(f.read(65536))
            if size > 65536:
                f.seek(-min(65536, size - 65536), 2)
                h.update(f.read(65536))
        return h.hexdigest()
    except Exception:
        return None

def main():
    apply_changes = "--apply" in sys.argv
    mode = "[EJECUCIÓN REAL]" if apply_changes else "[MODO SIMULACIÓN - DRY RUN]"
    
    print("=" * 80)
    print(f"  {mode} PURGA COMPLETA Y DEFINITIVA DE CAPTURAS/TABLAS ESPECÍFICAS")
    print("=" * 80)
    
    # 1. Compute target hashes for the 4 images
    target_hashes = {}
    for tp in TARGET_FILES_ON_F:
        tp_norm = os.path.normpath(tp)
        if os.path.exists(tp_norm):
            h = get_fast_hash(tp_norm)
            if h:
                target_hashes[h] = {
                    'filename': os.path.basename(tp_norm),
                    'size': os.path.getsize(tp_norm),
                    'original_path': tp_norm
                }
                
    if not target_hashes:
        print("Error: No se encontró ninguno de los archivos originales en F: para calcular su firma digital.")
        sys.exit(1)
        
    print(f"Firmas binarias calculadas para las {len(target_hashes)} imágenes objetivo.")
    for h, info in target_hashes.items():
        print(f"  - {info['filename']} ({info['size']} bytes) -> Hash: {h}")
        
    # 2. Scan targeted directories for duplicates
    print("\nBuscando copias idénticas en OneDrive, Dropbox y discos locales...")
    duplicates_found = []
    
    for sd in SEARCH_DIRS:
        if not os.path.exists(sd):
            continue
            
        print(f"Escaneando: {sd} ...")
        for root, dirs, files in os.walk(sd):
            # Skip hidden and system folders
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    fp = os.path.normpath(os.path.join(root, f))
                    try:
                        f_size = os.path.getsize(fp)
                        # Check size first before hashing to be ultra-fast!
                        matched_h = None
                        for h_val, info in target_hashes.items():
                            # allow small size tolerance or exact match
                            if abs(f_size - info['size']) <= 100: # allow metadata overhead differences
                                matched_h = h_val
                                break
                                
                        if matched_h:
                            # Verify with quick hash
                            real_hash = get_fast_hash(fp)
                            if real_hash == matched_h or real_hash in target_hashes:
                                h_key = real_hash or matched_h
                                duplicates_found.append({
                                    'path': fp,
                                    'filename': f,
                                    'size': f_size,
                                    'target_filename': target_hashes[h_key]['filename'],
                                    'hash': h_key
                                })
                    except Exception:
                        pass
                        
    total_copies = len(duplicates_found)
    print(f"\nTotal copias físicas encontradas en todo el sistema: {total_copies}")
    
    if total_copies == 0:
        print("No se encontraron copias para eliminar.")
        sys.exit(0)
        
    # Categorize by drive/location
    by_loc = {}
    for item in duplicates_found:
        path_low = item['path'].lower()
        cat = 'C:_Drive'
        if 'onedrive' in path_low:
            cat = 'OneDrive'
        elif 'dropbox' in path_low:
            cat = 'Dropbox'
        elif 'pictures' in path_low:
            cat = 'Pictures'
        elif 'downloads' in path_low:
            cat = 'Downloads'
        elif path_low.startswith('f:'):
            cat = 'F_Drive'
        by_loc.setdefault(cat, []).append(item)
        
    print("\n--- Distribución de copias por ubicación ---")
    for loc, items in by_loc.items():
        size_mb = sum(item['size'] for item in items) / (1024*1024)
        print(f"  - {loc:<15}: {len(items)} copias ({size_mb:.2f} MB)")
        
    # Details of copies
    print("\n--- Listado detallado de copias detectadas ---")
    for item in duplicates_found:
        print(f"  [{item['target_filename']}] -> {item['path']} ({item['size']} bytes)")
        
    # 3. Purging
    if apply_changes:
        print("\n" + "="*50)
        print("  EJECUTANDO ELIMINACIÓN REAL Y SINCRONIZACIÓN DE DB...")
        print("=" * 50)
        
        conn = sqlite3.connect(DB_PATH)
        deleted_physical = 0
        deleted_db = 0
        total_freed_bytes = 0
        
        try:
            conn.execute("BEGIN TRANSACTION;")
            
            for item in duplicates_found:
                fp = item['path']
                size = item['size']
                fn = item['filename']
                
                # A. Delete physical file
                if os.path.exists(fp):
                    try:
                        os.remove(fp)
                        deleted_physical += 1
                        total_freed_bytes += size
                        print(f"  [BORRADO] {fp}")
                    except Exception as e:
                        print(f"  [Error] No se pudo borrar {fp}: {e}")
                        continue
                else:
                    deleted_physical += 1
                    total_freed_bytes += size
                    
                # B. Delete database entry
                cursor = conn.execute("DELETE FROM photos WHERE filename = ? AND file_size = ?", (fn, size))
                deleted_db += cursor.rowcount
                
            conn.commit()
            print("\n" + "="*50)
            print("  PURGA COMPLETADA CON ÉXITO")
            print("=" * 50)
            print(f"  - Archivos físicos eliminados:        {deleted_physical}/{total_copies}")
            print(f"  - Registros de base de datos borrados: {deleted_db}")
            print(f"  - Espacio total de disco liberado:     {total_freed_bytes / (1024*1024):.2f} MB")
            print("=" * 50)
            
        except Exception as e:
            conn.rollback()
            print(f"\n[ERROR CRÍTICO] Falló la eliminación: {e}")
            sys.exit(1)
        finally:
            conn.close()
            
    else:
        total_space = sum(item['size'] for item in duplicates_found) / (1024*1024)
        print("\n" + "="*50)
        print("  AVISO: Modo simulación activo. No se hicieron cambios permanentes.")
        print(f"  - Si ejecutas con el flag '--apply', se eliminarán {total_copies} archivos físicos.")
        print(f"  - Se liberarán: {total_space:.2f} MB de almacenamiento total.")
        print("  Para aplicar la purga, ejecuta:")
        print("    python apps/backend/scripts/purge_targeted_sheets.py --apply")
        print("="*50)

if __name__ == '__main__':
    main()
