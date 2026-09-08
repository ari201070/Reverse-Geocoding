import os
import shutil
import sqlite3
import hashlib
from datetime import datetime, timedelta

# Configuración de Rutas de la Unidad F:
DB_PATH = r"F:\photo_catalog.db"
SRC_BASE_DIR = r"F:\Fotos_Organizadas\Scan_Pics_Extraidas"
DST_DIR = r"F:\1983\06-Junio"

# Fallbacks locales si no estás en la máquina física con la unidad F:
if not os.path.exists("F:\\"):
    DB_PATH = "photo_catalog.db"
    SRC_BASE_DIR = "Scan_Pics_Extraidas"
    DST_DIR = os.path.join("1983", "06-Junio")

# Coordenadas exactas del Centro Cívico de San Carlos de Bariloche
BARILOCHE_LAT = -41.133433
BARILOCHE_LNG = -71.311417
LOCATION_NAME = "Centro Cívico - Bariloche"
LOCATION_ADDRESS = "Centro Cívico, San Carlos de Bariloche, Río Negro, Argentina"
CITY = "San Carlos de Bariloche"
PROVINCE = "Río Negro"
COUNTRY = "Argentina"

# Fecha histórica base (junio de 1983)
START_DATE = datetime(1983, 6, 15, 10, 0, 0)

def get_sha256(file_path):
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"Error calculando hash para {file_path}: {e}")
        return None

def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en '{DB_PATH}'")
        return

    # Crear carpeta de destino si no existe
    if not os.path.exists(DST_DIR):
        os.makedirs(DST_DIR)
        print(f"[CARPETA CREADA] Destino listo en: {DST_DIR}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Inspección dinámica de columnas de la tabla de fotos
    cursor.execute("PRAGMA table_info(photos)")
    columns = [col[1] for col in cursor.fetchall()]
    lat_col = 'latitude' if 'latitude' in columns else 'lat'
    lng_col = 'longitude' if 'longitude' in columns else 'lng'
    hash_col = 'sha256' if 'sha256' in columns else ('file_hash' if 'file_hash' in columns else 'hash')
    path_col = 'final_path' if 'final_path' in columns else ('file_path' if 'file_path' in columns else 'path')

    moved_total = 0
    indexed_total = 0
    skipped_dup_total = 0
    global_photo_idx = 0

    # Recorrer las carpetas del 1 al 5
    for i in range(1, 6):
        folder_name = f"bariloche_primaria_{i}"
        src_dir = os.path.join(SRC_BASE_DIR, folder_name)
        
        if not os.path.exists(src_dir):
            print(f"\n[AVISO] No se encontró el directorio origen: {src_dir}. Saltando...")
            continue
            
        print(f"\nProcessing Folder: {folder_name}...")
        files = [f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        print(f"  -> Encontradas {len(files)} fotos para mover e indexar.")

        for file_name in sorted(files):
            src_path = os.path.join(src_dir, file_name)
            dst_path = os.path.join(DST_DIR, file_name)
            
            # Calcular hash en origen antes de mover
            sha256 = get_sha256(src_path)
            if not sha256:
                continue

            file_size = os.path.getsize(src_path)

            # Mover archivo físico al destino final
            try:
                shutil.move(src_path, dst_path)
                moved_total += 1
            except Exception as e:
                print(f"  Error al mover {file_name}: {e}")
                continue

            # Comprobar duplicación de hash en la base de datos
            cursor.execute(f"SELECT id FROM photos WHERE {hash_col} = ?", (sha256,))
            existing = cursor.fetchone()
            if existing:
                skipped_dup_total += 1
                continue

            # Generar estampa de tiempo incremental e irreversible para junio de 1983
            date_taken_dt = START_DATE + timedelta(hours=global_photo_idx * 2)
            date_taken_str = date_taken_dt.strftime("%Y-%m-%d %H:%M:%S")
            global_photo_idx += 1

            # Preparar objeto de inserción adaptativo al esquema
            insert_data = {}
            if path_col in columns:
                insert_data[path_col] = dst_path
            if 'original_path' in columns:
                insert_data['original_path'] = src_path
            if 'filename' in columns:
                insert_data['filename'] = file_name
            if 'file_size' in columns:
                insert_data['file_size'] = file_size
            if 'date_taken' in columns:
                insert_data['date_taken'] = date_taken_str
            if 'year' in columns:
                insert_data['year'] = 1983
            if 'month_folder' in columns:
                insert_data['month_folder'] = "06-Junio"
            if 'folder_source' in columns:
                insert_data['folder_source'] = "06-Junio"
            if lat_col in columns:
                insert_data[lat_col] = BARILOCHE_LAT
            if lng_col in columns:
                insert_data[lng_col] = BARILOCHE_LNG
            if 'location_name' in columns:
                insert_data['location_name'] = LOCATION_NAME
            if 'location_address' in columns:
                insert_data['location_address'] = LOCATION_ADDRESS
            if 'city' in columns:
                insert_data['city'] = CITY
            if 'province' in columns:
                insert_data['province'] = PROVINCE
            if 'country' in columns:
                insert_data['country'] = COUNTRY
            if hash_col in columns:
                insert_data[hash_col] = sha256
            if 'is_duplicate' in columns:
                insert_data['is_duplicate'] = 0
            if 'location_source' in columns:
                insert_data['location_source'] = 'MANUAL'
            if 'date_source' in columns:
                insert_data['date_source'] = 'MANUAL_HISTORICAL'

            fields = list(insert_data.keys())
            placeholders = ", ".join(["?"] * len(fields))
            query = f"INSERT INTO photos ({', '.join(fields)}) VALUES ({placeholders})"

            try:
                cursor.execute(query, tuple(insert_data.values()))
                indexed_total += 1
            except Exception as e:
                print(f"    Error de inserción en DB para {file_name}: {e}")

        # Intentar borrar la carpeta de origen si ya quedó vacía tras el movimiento
        try:
            if not os.listdir(src_dir):
                os.rmdir(src_dir)
                print(f"  [LIMPIEZA] Carpeta vacía eliminada con éxito: {folder_name}")
        except Exception:
            pass

    conn.commit()
    conn.close()

    print("\n==================================================")
    print("PROCESO DE CONSOLIDACIÓN COMPLETO (LOTES 1-5):")
    print(f" - Fotos totales movidas físicamente a 1983\\06-Junio: {moved_total}")
    print(f" - Fotos nuevas registradas en base de datos: {indexed_total}")
    print(f" - Fotos omitidas en DB por duplicación de hash: {skipped_dup_total}")
    print("==================================================")

if __name__ == "__main__":
    main()
