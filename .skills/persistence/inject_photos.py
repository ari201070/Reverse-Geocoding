import sqlite3
import os
import sys
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    print("piexif no encontrado. Instalando...")
    os.system(f"{sys.executable} -m pip install piexif")
    try:
        import piexif
        PIEXIF_AVAILABLE = True
    except ImportError:
        PIEXIF_AVAILABLE = False

PHOTO_EXTENSIONS = ('.jpg', '.jpeg', '.heic', '.png')
COMMIT_EVERY = 500  # Commit cada N archivos para evitar bloqueos

def get_date_taken(file_path):
    """Extrae DateTimeOriginal del EXIF. Fallback a fecha de modificacion del archivo."""
    if PIEXIF_AVAILABLE and file_path.lower().endswith(('.jpg', '.jpeg')):
        try:
            exif_dict = piexif.load(file_path)
            exif = exif_dict.get("Exif", {})
            date_bytes = exif.get(piexif.ExifIFD.DateTimeOriginal)
            if date_bytes:
                d = date_bytes.decode('utf-8')
                # Formato EXIF: "YYYY:MM:DD HH:MM:SS" -> "YYYY-MM-DD HH:MM:SS"
                return d[:10].replace(':', '-') + d[10:]
        except Exception:
            pass
    try:
        ts = os.path.getmtime(file_path)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def discover_photo_folders(roots):
    """Valida que existan los roots y devuelve los que están disponibles."""
    valid = []
    for r in roots:
        if os.path.exists(r):
            valid.append(r)
        else:
            print(f"  [no disponible] {r}")
    return valid

def main():
    db_path = r"C:\Users\flier\.gemini\antigravity\scratch\Reverse-Geocoding\photo_catalog.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # 1. Crear tabla photos si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path   TEXT UNIQUE NOT NULL,
            filename    TEXT,
            date_taken  TEXT,
            latitude    REAL,
            longitude   REAL,
            location_name TEXT,
            city        TEXT,
            country     TEXT,
            date_source TEXT DEFAULT 'SCAN'
        )
    ''')
    conn.commit()
    print("Tabla 'photos' verificada/creada OK.\n")

    # 2. Carpetas a escanear (se agregan en orden de prioridad)
    candidate_roots = [
        "F:\\",
        "G:\\",
        r"F:\Fotos",
        r"G:\Fotos",
        r"F:\Pictures",
        r"G:\Pictures",
    ]
    print("=== PASO 1: Verificando unidades fisicas ===")
    valid_roots = discover_photo_folders(candidate_roots)

    if not valid_roots:
        print("\nAVISO: Ninguna unidad de fotos (F: / G:) esta disponible en este momento.")
        print("La tabla 'photos' fue creada correctamente.")
        print("Vuelve a ejecutar este script cuando los discos esten montados.")
        conn.close()
        return

    # Evitar sub-escaneos redundantes (si F:\ ya esta, no escanear F:\Fotos por separado)
    seen_drives = set()
    final_roots = []
    for r in valid_roots:
        drive = os.path.splitdrive(r)[0].upper()
        root_stripped = r.rstrip('\\')
        drive_root = drive + "\\"
        if drive_root in [x.rstrip('\\') + '\\' for x in final_roots]:
            print(f"  [omitido - drive raiz ya incluido] {r}")
            continue
        final_roots.append(r)
    print(f"\nCarpetas activas a escanear: {final_roots}")

    # 3. Escaneo e inyeccion
    inserted = 0
    updated = 0
    errors = 0
    total_scanned = 0
    ops_since_commit = 0

    print("\n=== PASO 2: Escaneando fotos ===")
    for root_folder in final_roots:
        print(f"\nEscaneando: {root_folder}")
        folder_count = 0
        for dirpath, dirnames, files in os.walk(root_folder):
            # Omitir carpetas de sistema
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in
                           ('System Volume Information', '$RECYCLE.BIN', 'Windows', 'Program Files')]
            photo_files = [f for f in files if f.lower().endswith(PHOTO_EXTENSIONS)]
            if not photo_files:
                continue

            for fname in photo_files:
                fpath = os.path.join(dirpath, fname)
                total_scanned += 1
                folder_count += 1
                date_taken = get_date_taken(fpath)

                try:
                    cursor.execute("SELECT id FROM photos WHERE file_path = ?", (fpath,))
                    exists = cursor.fetchone()
                    cursor.execute('''
                        INSERT INTO photos (file_path, filename, date_taken, date_source)
                        VALUES (?, ?, ?, 'SCAN')
                        ON CONFLICT(file_path) DO UPDATE SET
                            date_taken = excluded.date_taken
                    ''', (fpath, fname, date_taken))

                    if exists:
                        updated += 1
                    else:
                        inserted += 1
                    ops_since_commit += 1

                    if ops_since_commit >= COMMIT_EVERY:
                        conn.commit()
                        ops_since_commit = 0
                        print(f"  ... {total_scanned} archivos procesados (commit parcial)")

                except Exception as e:
                    errors += 1
                    if errors <= 10:
                        print(f"  Error: {fpath}: {e}")

        print(f"  -> {folder_count} fotos encontradas en {root_folder}")

    # Commit final
    conn.commit()
    conn.close()

    print("\n=== REPORTE FINAL DE INYECCION DE RUTAS ===")
    print(f"Archivos escaneados:           {total_scanned}")
    print(f"Registros nuevos insertados:   {inserted}")
    print(f"Registros actualizados:        {updated}")
    print(f"Errores:                       {errors}")
    print("La tabla 'photos' esta lista para vinculacion espaciotemporal con known_places.")

if __name__ == '__main__':
    main()
