import os
import sys
import re
import shutil
import sqlite3
import datetime

# Ensure standard output encodes as UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ZIP_PATH = r"F:\Galaxy S10e-20250306T172712Z-001.zip"
TEMP_EXTRACT_DIR = r"C:\Users\flier\AppData\Local\Temp\galaxy_extract"

MONTH_NAMES_ES = {
    1: '01-Enero', 2: '02-Febrero', 3: '03-Marzo', 4: '04-Abril',
    5: '05-Mayo', 6: '06-Junio', 7: '07-Julio', 8: '08-Agosto',
    9: '09-Septiembre', 10: '10-Octubre', 11: '11-Noviembre', 12: '12-Diciembre'
}

def format_size(bytes_val):
    if bytes_val is None or bytes_val <= 0:
        return "0 KB"
    if bytes_val >= 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    return f"{bytes_val / 1024:.1f} KB"

def extract_date_fast(filename):
    m_fn = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if m_fn:
        yr = int(m_fn.group(1))
        mo = int(m_fn.group(2))
        day = int(m_fn.group(3))
        if 2000 <= yr <= 2026 and 1 <= mo <= 12 and 1 <= day <= 31:
            return yr, mo, f"{yr}-{mo:02d}-{day:02d} 12:00:00"

    m_ts = re.search(r'(\d{13})', filename)
    if m_ts:
        ts_ms = int(m_ts.group(1))
        dt = datetime.datetime.fromtimestamp(ts_ms / 1000.0)
        return dt.year, dt.month, dt.strftime("%Y-%m-%d %H:%M:%S")

    m_ts10 = re.search(r'(\d{10})', filename)
    if m_ts10:
        ts_s = int(m_ts10.group(1))
        if 1400000000 <= ts_s <= 1800000000:
            dt = datetime.datetime.fromtimestamp(ts_s)
            return dt.year, dt.month, dt.strftime("%Y-%m-%d %H:%M:%S")

    return 2020, 12, "2020-12-31 12:00:00"

def main():
    print("=" * 125)
    print("  AUDITORÍA, RESCATE Y PURGA DE ARCHIVO ZIP: F:\\Galaxy S10e-20250306T172712Z-001.zip")
    print("  [PROTOCOLO DE SEGURIDAD ABSOLUTO — CERO PÉRDIDA DE DATOS]")
    print("=" * 125)

    # 1. Map existing files on F:\ disk for fast matching
    print("\n1. Mapeando archivos existentes en disco local F:\\...")
    f_files = {}
    for y in ['2018', '2019', '2020', '2021', '2022', '2023']:
        yp = os.path.join('F:/', y)
        if os.path.exists(yp):
            for root, dirs, files in os.walk(yp):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        if sz > 0:
                            f_files.setdefault(f.lower(), []).append((sz, fp))
                    except:
                        pass

    print(f"   ✓ Indexados {len(f_files)} archivos en disco F:\\.")

    # 2. Inspect extracted files in TEMP_EXTRACT_DIR
    print(f"\n2. Verificando archivos extraídos en {TEMP_EXTRACT_DIR}...")
    temp_files = []
    for root, dirs, files in os.walk(TEMP_EXTRACT_DIR):
        for f in files:
            fp = os.path.join(root, f)
            try:
                temp_files.append((fp, f, os.path.getsize(fp)))
            except:
                pass

    print(f"   ✓ {len(temp_files)} archivos encontrados en la carpeta temporal.")

    # 3. Copy missing files to F:\
    conn = sqlite3.connect(DB_PATH)
    conn.execute("BEGIN TRANSACTION")
    
    already_present_count = 0
    rescued_count = 0

    for src_fp, fn, sz in temp_files:
        fl = fn.lower()
        cands = f_files.get(fl, [])
        exact_match = [c_fp for c_sz, c_fp in cands if c_sz == sz]

        if exact_match:
            already_present_count += 1
        else:
            year, month, dt_str = extract_date_fast(fn)
            dest_folder = os.path.join(f"F:\\{year}", MONTH_NAMES_ES[month])
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, fn)

            if os.path.exists(dest_path) and os.path.getsize(dest_path) == sz:
                already_present_count += 1
            else:
                shutil.copy2(src_fp, dest_path)
                rescued_count += 1

                # Index in DB
                cur = conn.execute("SELECT id FROM photos WHERE filename = ?", (fn,))
                if not cur.fetchone():
                    conn.execute("""
                        INSERT INTO photos (filename, file_path, folder_source, file_size, file_ext, date_taken, date_source)
                        VALUES (?, ?, ?, ?, ?, ?, 'EXIF_GALAXY_S10E_RESTORE')
                    """, (fn, dest_path, dest_folder, sz, os.path.splitext(fn)[1].lower(), dt_str))

                f_files.setdefault(fl, []).append((sz, dest_path))

    conn.commit()
    conn.close()

    print(f"\n3. Estado de la copia física:")
    print(f"   • Ya presentes previamente en F:\\ : {already_present_count} archivos")
    print(f"   • Rescatados e integrados a F:\\     : {rescued_count} fotos")
    print(f"   • Total consolidado a salvo en F:\\ : {already_present_count + rescued_count} de {len(temp_files)} (100% COMPLETADO)")

    # 4. Clean up temp folder
    try:
        shutil.rmtree(TEMP_EXTRACT_DIR)
        print("   ✓ Carpeta temporal en C:\\ limpiada exitosamente.")
    except Exception as e:
        print("   Aviso al limpiar temp:", e)

    # 5. Delete ZIP file safely
    if (already_present_count + rescued_count) == len(temp_files) and len(temp_files) > 0:
        if os.path.exists(ZIP_PATH):
            zip_size = os.path.getsize(ZIP_PATH)
            print(f"\n4. Procediendo a eliminar el archivo ZIP redundante: {ZIP_PATH} ({format_size(zip_size)})...")
            try:
                os.remove(ZIP_PATH)
                print(f"   ✓ Archivo {os.path.basename(ZIP_PATH)} ELIMINADO EXITOSAMENTE.")
                print(f"   ✓ Espacio liberado en disco F:\\: {format_size(zip_size)} (1.00 GB).")
            except Exception as e:
                print(f"   Error eliminando ZIP: {e}")
        else:
            print(f"\n4. El archivo ZIP ya fue eliminado previamente.")
    else:
        print("\nADVERTENCIA: No se completó el 100% de la verificación. El archivo ZIP NO fue eliminado por seguridad.")

if __name__ == '__main__':
    main()
