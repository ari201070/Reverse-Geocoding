import os
import re
import shutil
import hashlib
from PIL import Image
from datetime import datetime

SRC_QUARANTINE = r"F:\Deduplication_Quarantine_Backup"
TRASH_PREFIX = r"F:\.Papelera_Deduplicacion"
IMG_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif', '.mp4')

def get_sha256(file_path):
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return None

def get_capture_year(file_path):
    # 1. Intentar EXIF original
    if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        try:
            with Image.open(file_path) as img:
                exif = img._getexif()
                if exif:
                    # 36867 = DateTimeOriginal, 306 = DateTime
                    for tag in [36867, 306]:
                        date_str = exif.get(tag)
                        if date_str and isinstance(date_str, str):
                            match = re.match(r'^(\d{4})', date_str.strip())
                            if match:
                                year = int(match.group(1))
                                if 2000 <= year <= 2026:
                                    return year
        except Exception:
            pass

    # 2. Intentar Regex en el nombre del archivo (YYYY-MM-DD o YYYYMMDD)
    filename = os.path.basename(file_path)
    match = re.search(r'(\d{4})[-.:_](\d{2})[-.:_](\d{2})', filename)
    if match:
        year = int(match.group(1))
        if 2000 <= year <= 2026:
            return year

    # 3. Fallback a mtime si el año es coherente
    try:
        mtime = os.path.getmtime(file_path)
        dt = datetime.fromtimestamp(mtime)
        if 2000 <= dt.year <= 2026:
            return dt.year
    except Exception:
        pass

    return None

def reverse_consolidation():
    if not os.path.exists(SRC_QUARANTINE):
        print(f"La carpeta origen {SRC_QUARANTINE} no existe. Proceso cancelado.")
        return

    print("--- PASO 1: ESCANEANDO PAPELERAS HISTÓRICAS EXISTENTES ---")
    existing_hashes = set()
    
    # Escanear cualquier carpeta que empiece con F:\.Papelera_Deduplicacion
    for item in os.listdir("F:\\"):
        if item.startswith(".Papelera_Deduplicacion"):
            folder_path = os.path.join("F:\\", item)
            if os.path.isdir(folder_path):
                print(f"Escaneando hashes existentes en: {item}")
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith(IMG_EXTENSIONS):
                            path = os.path.join(root, file)
                            f_hash = get_sha256(path)
                            if f_hash:
                                existing_hashes.add(f_hash)

    print(f"Total de fotos únicas ya resguardadas en papeleras: {len(existing_hashes)}")

    print("\n--- PASO 2: VACIANDO DEDUPLICATION_QUARANTINE_BACKUP ---")
    moved_count = 0
    deleted_siamese_count = 0

    for root, _, files in os.walk(SRC_QUARANTINE):
        for file in files:
            if not file.lower().endswith(IMG_EXTENSIONS):
                continue
                
            src_path = os.path.join(root, file)
            f_hash = get_sha256(src_path)
            
            if not f_hash:
                continue

            # Determinar el año real
            year = get_capture_year(src_path)
            if year:
                dest_dir = f"{TRASH_PREFIX}{year}"
            else:
                dest_dir = f"{TRASH_PREFIX}_Otros"

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            # Si el SHA-256 ya está en la papelera, borramos directamente la copia de la cuarentena molesta (es un siamés)
            if f_hash in existing_hashes:
                print(f"  [DEL SIAMESE] Borrando copia idéntica: {file}")
                try:
                    os.remove(src_path)
                    deleted_siamese_count += 1
                except Exception as e:
                    print(f"  Error borrando siamés: {e}")
                continue

            # Mover el archivo a su papelera correspondiente
            dest_path = os.path.join(dest_dir, file)
            
            # Evitar colisión de nombres
            base_name, ext = os.path.splitext(file)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(dest_dir, f"{base_name}_{counter}{ext}")
                counter += 1

            print(f"  [MOVE] {file} -> {os.path.basename(dest_dir)}")
            try:
                shutil.move(src_path, dest_path)
                existing_hashes.add(f_hash)
                moved_count += 1
            except Exception as e:
                print(f"  Error moviendo archivo: {e}")

    print("\n--- PASO 3: LIMPIEZA FINAL DE CARPETAS VACÍAS ---")
    
    # 1. Eliminar recursivamente la carpeta temporal de cuarentena si quedó vacía
    if os.path.exists(SRC_QUARANTINE):
        try:
            shutil.rmtree(SRC_QUARANTINE)
            print(f"  [RMDIR] Carpeta {SRC_QUARANTINE} eliminada exitosamente.")
        except Exception as e:
            print(f"  Error al eliminar {SRC_QUARANTINE}: {e}")

    # 2. Barrer carpetas fantasmas vacías específicas en F:\
    ghost_folders = [r"F:\2005\11-Noviembre", r"F:\2005", r"F:\2067\06-Junio", r"F:\2067"]
    for folder in ghost_folders:
        if os.path.exists(folder):
            try:
                if not os.listdir(folder):
                    os.rmdir(folder)
                    print(f"  [RMDIR] Carpeta fantasma eliminada: {folder}")
            except Exception:
                pass

    print("\n============================================================")
    print("CONSOLIDACIÓN DE PAPELERA TERMINADA:")
    print(f" - Fotos únicas movidas a su .Papelera_Deduplicacion correspondiente: {moved_count}")
    print(f" - Fotos siamesas (duplicados exactos) eliminadas directamente: {deleted_siamese_count}")
    print(" - Carpeta Deduplication_Quarantine_Backup BORRADA por completo.")
    print("============================================================")

if __name__ == "__main__":
    reverse_consolidation()
