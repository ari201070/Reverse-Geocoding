import os
import sys
import io
import sqlite3
import shutil
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

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
SIN_VIAJE_ROOT = r"F:\Fotos_Organizadas\Sin_Viaje"
F_DRIVE_ROOT = r"F:\\"

MONTH_PREFIXES = {
    "enero": "01-Enero",
    "febrero": "02-Febrero",
    "marzo": "03-Marzo",
    "abril": "04-Abril",
    "mayo": "05-Mayo",
    "junio": "06-Junio",
    "julio": "07-Julio",
    "agosto": "08-Agosto",
    "septiembre": "09-Septiembre",
    "octubre": "10-Octubre",
    "noviembre": "11-Noviembre",
    "diciembre": "12-Diciembre"
}

def parse_date_only(dt_str):
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    if len(dt_str) >= 10:
        date_part = dt_str[:10].replace(':', '-').replace('/', '-')
        if len(date_part) == 10 and date_part[0].isdigit() and date_part[4] == '-' and date_part[7] == '-':
            return date_part
    return None

def get_prefixed_month(month_str):
    if not month_str:
        return "01-Enero"
    m_clean = month_str.lower().strip()
    # If already prefixed (e.g. "03-Marzo"), return it
    if m_clean and m_clean[0].isdigit() and '-' in m_clean:
        # capitalize after the dash
        parts = m_clean.split('-', 1)
        return f"{parts[0]}-{parts[1].capitalize()}"
    # Map plain month to prefixed month
    if m_clean in MONTH_PREFIXES:
        return MONTH_PREFIXES[m_clean]
    return "01-Enero"

def get_exif_date_taken(file_path):
    if not PILLOW_AVAILABLE:
        return None
    try:
        img = Image.open(file_path)
        exif = img._getexif()
        if not exif:
            return None
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal" or tag == "DateTime":
                if isinstance(value, bytes):
                    value = value.decode(errors="ignore")
                return str(value).strip()
    except Exception:
        pass
    return None

def standardize_path(path_str, filename):
    """
    Translates a plain path like F:\2009\Diciembre\filename.jpg to prefixed F:\2009\12-Diciembre\filename.jpg
    Also forces F: drive for all destination paths.
    """
    if not path_str:
        return None
    path_clean = path_str.replace("\\", "/")
    
    # Force F: drive for all destinations to prevent G: drive mount errors
    if path_clean.lower().startswith("g:"):
        path_clean = "F:" + path_clean[2:]
        
    parts = path_clean.split('/')
    
    if len(parts) >= 4:
        month_part = parts[2]
        prefixed = get_prefixed_month(month_part)
        parts[2] = prefixed
        return os.path.normpath("/".join(parts))
    else:
        return None

def main():
    apply_changes = "--apply" in sys.argv
    mode = "[EJECUCIÓN REAL]" if apply_changes else "[MODO SIMULACIÓN - DRY RUN]"
    
    print("=" * 80)
    print(f"  {mode} REORGANIZACIÓN FÍSICA DE 'Sin_Viaje' ↔ CARPETAS DE FECHA")
    print(f"  Origen:         {SIN_VIAJE_ROOT}")
    print(f"  Base de datos:  {DB_PATH}")
    print("=" * 80)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    if not os.path.exists(SIN_VIAJE_ROOT):
        print(f"Aviso: El directorio {SIN_VIAJE_ROOT} ya no existe o ya fue removido.")
        sys.exit(0)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # 1. Walk through F:\Fotos_Organizadas\Sin_Viaje recursively
        moved_count = 0
        ingested_count = 0
        unmatched_count = 0
        skipped_count = 0
        
        print("\nEscaneando archivos físicos...")
        
        # We will iterate through files on disk
        for root, dirs, files in os.walk(SIN_VIAJE_ROOT):
            for f in files:
                src_path = os.path.join(root, f)
                file_size = os.path.getsize(src_path)
                
                # Query DB to find matching record by filename and size
                cursor = conn.execute(
                    "SELECT id, file_path, date_taken FROM photos WHERE filename = ? AND file_size = ?", 
                    (f, file_size)
                )
                db_matches = cursor.fetchall()
                
                if len(db_matches) == 1:
                    row = db_matches[0]
                    pid = row['id']
                    db_path = row['file_path']
                    
                    # Standardize destination path to use month prefixes
                    dst_path = standardize_path(db_path, f)
                    if not dst_path:
                        # Fallback if database path format is non-standard
                        year_folder = os.path.basename(os.path.dirname(src_path)) # parent of file is year or month?
                        # F:\Fotos_Organizadas\Sin_Viaje\2009\filename -> parent is '2009'
                        if year_folder.isdigit() and len(year_folder) == 4:
                            dst_path = os.path.normpath(f"F:/{year_folder}/01-Enero/{f}")
                        else:
                            dst_path = os.path.normpath(f"F:/2009/01-Enero/{f}") # default fallback
                            
                    dst_dir = os.path.dirname(dst_path)
                    
                    if not apply_changes:
                        if moved_count < 10:
                            print(f"[SIMULACIÓN] Mover: {os.path.relpath(src_path, SIN_VIAJE_ROOT)}")
                            print(f"             A:     {dst_path}")
                            print(f"             DB ID: {pid} (Ruta DB actual: {db_path})")
                    else:
                        os.makedirs(dst_dir, exist_ok=True)
                        # Check if destination file already exists
                        if os.path.exists(dst_path):
                            # If content is identical, just delete original, else append suffix
                            if os.path.getsize(dst_path) == file_size:
                                os.remove(src_path)
                            else:
                                base, ext = os.path.splitext(f)
                                dst_path = os.path.join(dst_dir, f"{base}_dup{ext}")
                                shutil.move(src_path, dst_path)
                        else:
                            shutil.move(src_path, dst_path)
                            
                        # Update database path
                        conn.execute("UPDATE photos SET file_path = ? WHERE id = ?", (dst_path, pid))
                        
                    moved_count += 1
                    
                elif len(db_matches) > 1:
                    # Multiple matches (exact filename and size). To be safe, skip or use first match
                    row = db_matches[0]
                    pid = row['id']
                    db_path = row['file_path']
                    dst_path = standardize_path(db_path, f)
                    
                    if dst_path:
                        dst_dir = os.path.dirname(dst_path)
                        if apply_changes:
                            os.makedirs(dst_dir, exist_ok=True)
                            if not os.path.exists(dst_path):
                                shutil.move(src_path, dst_path)
                            else:
                                os.remove(src_path)
                            conn.execute("UPDATE photos SET file_path = ? WHERE id = ?", (dst_path, pid))
                        moved_count += 1
                    else:
                        skipped_count += 1
                        
                else:
                    # NOT registered in database!
                    # Let's extract year/month of file and ingest it
                    # Try to get EXIF date
                    exif_date = get_exif_date_taken(src_path)
                    year = "2009" # default fallback
                    month_folder = "01-Enero"
                    
                    if exif_date:
                        date_parts = parse_date_only(exif_date)
                        if date_parts:
                            year = date_parts.split('-')[0]
                            month_num = date_parts.split('-')[1]
                            # Map month number to prefix
                            month_names = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                            try:
                                month_folder = get_prefixed_month(month_names[int(month_num) - 1])
                            except: pass
                    else:
                        # try to guess from physical parent folder F:\Fotos_Organizadas\Sin_Viaje\2009 -> 2009
                        parent_dir = os.path.basename(os.path.dirname(src_path))
                        if parent_dir.isdigit() and len(parent_dir) == 4:
                            year = parent_dir
                            
                    dst_path = os.path.normpath(f"F:/{year}/{month_folder}/{f}")
                    dst_dir = os.path.dirname(dst_path)
                    
                    if not apply_changes:
                        if unmatched_count < 10:
                            print(f"[SIMULACIÓN-NUEVA] Ingestar: {os.path.relpath(src_path, SIN_VIAJE_ROOT)}")
                            print(f"                   A:        {dst_path} (Fecha EXIF: {exif_date or 'No'})")
                    else:
                        os.makedirs(dst_dir, exist_ok=True)
                        if os.path.exists(dst_path):
                            if os.path.getsize(dst_path) == file_size:
                                os.remove(src_path)
                            else:
                                base, ext = os.path.splitext(f)
                                dst_path = os.path.join(dst_dir, f"{base}_dup{ext}")
                                shutil.move(src_path, dst_path)
                        else:
                            shutil.move(src_path, dst_path)
                            
                        # Ingest into DB
                        ext = os.path.splitext(f)[1].upper()
                        conn.execute("""
                            INSERT INTO photos (file_path, folder_source, filename, file_size, file_ext, date_taken, date_source)
                            VALUES (?, 'unified_disk', ?, ?, ?, ?, ?)
                        """, (dst_path, f, file_size, ext, exif_date or f"{year}-01-01 00:00:00", 'exif' if exif_date else 'filesystem_mtime'))
                        
                    ingested_count += 1
                    
        if apply_changes:
            conn.commit()
            print("\n" + "="*50)
            print("  PROCESAMIENTO FÍSICO COMPLETADO")
            print("=" * 50)
            print(f"  Archivos movidos y actualizados en DB: {moved_count}")
            print(f"  Archivos nuevos ingresados y movidos:  {ingested_count}")
            print(f"  Archivos omitidos por seguridad:       {skipped_count}")
            
            # Clean up empty directories in F:\Fotos_Organizadas\Sin_Viaje
            print("\nVaciando directorios temporales de Sin_Viaje...")
            for pass_num in range(4):
                for root, dirs, files in os.walk(SIN_VIAJE_ROOT, topdown=False):
                    for d in dirs:
                        dir_path = os.path.join(root, d)
                        try:
                            if not os.listdir(dir_path):
                                os.rmdir(dir_path)
                        except: pass
            try:
                if not os.listdir(SIN_VIAJE_ROOT):
                    os.rmdir(SIN_VIAJE_ROOT)
                    print("¡Carpeta F:\\Fotos_Organizadas\\Sin_Viaje eliminada completamente!")
                else:
                    print("Nota: Quedaron algunos archivos no procesados en Sin_Viaje. No se eliminó la raíz.")
            except Exception as e:
                print(f"No se pudo eliminar la carpeta raíz: {e}")
        else:
            print("\n" + "="*50)
            print("  RESUMEN DE SIMULACIÓN (DRY RUN)")
            print("=" * 50)
            print(f"  Archivos que se moverán y actualizarán en DB: {moved_count}")
            print(f"  Archivos nuevos que se ingresarán y moverán:  {ingested_count}")
            print(f"  Archivos que se omitirán por seguridad:       {skipped_count}")
            print("\nPara ejecutar la reorganización real y mover los archivos físicos, ejecuta:")
            print("  python apps/backend/scripts/reorganize_sin_viaje.py --apply")
            
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR CRÍTICO] Falló la reorganización: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
