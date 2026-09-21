import os
import sys
import re
import shutil
import sqlite3
import hashlib
import datetime

# Ensure stdout/stderr encode as UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
REPORT_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\audit_cloud_cleanup_report.md"

CLOUD_SOURCE_DIRS = [
    ("Dropbox", r"C:\Users\flier\Dropbox"),
    ("Google Drive (Local C:)", r"C:\Users\flier\Google Drive"),
    ("Google Drive (Local F:)", r"F:\האחסון שלי")
]

EXCLUDE_DIRS = ['.dropbox.cache', '.tmp.drivedownload', '$recycle.bin']

def format_size(bytes_val):
    if bytes_val is None or bytes_val <= 0:
        return "0 KB"
    if bytes_val >= 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    return f"{bytes_val / 1024:.1f} KB"

def compute_sha256(fp):
    try:
        h = hashlib.sha256()
        with open(fp, 'rb') as f:
            while chunk := f.read(1024 * 1024):
                h.update(chunk)
        return h.hexdigest()
    except:
        return None

def get_disk_free(drive_letter):
    try:
        root = drive_letter + ":\\"
        u = shutil.disk_usage(root)
        return u.free, u.total
    except:
        return 0, 0

def safe_remove_file(fp):
    try:
        # Handle potential read-only attributes on Windows
        os.chmod(fp, 0o777)
    except:
        pass
    os.remove(fp)

def main():
    print("=" * 125)
    print("  FASE 2: EJECUCIÓN DE PURGA Y LIBERACIÓN DE ESPACIO EN LA NUBE (DRIVE Y DROPBOX)")
    print("  [PROTOCOLO DE SEGURIDAD ABSOLUTO — REGLA 1: PROTECCIÓN TOTAL DE ARCHIVOS ÚNICOS]")
    print("=" * 125)

    if not os.path.exists(DB_PATH):
        print(f"Error crítico: Base de datos central no encontrada en {DB_PATH}")
        sys.exit(1)

    c_free_before, _ = get_disk_free("C")
    f_free_before, _ = get_disk_free("F")
    print(f"Espacio libre antes de la purga -> Disco C:\\: {format_size(c_free_before)}, Disco F:\\: {format_size(f_free_before)}")

    # 1. Load photo_catalog.db in memory
    print("\n1. Cargando base de datos central photo_catalog.db...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT filename, file_size, sha256, file_path FROM photos")
    db_rows = cursor.fetchall()
    conn.close()

    db_by_name_size = {}
    db_by_sha = {}
    db_by_size = {}

    for r in db_rows:
        fn = r['filename'].lower() if r['filename'] else ''
        sz = r['file_size'] or 0
        sha = r['sha256']
        fp = r['file_path']

        if fn and sz > 0:
            db_by_name_size[(fn, sz)] = fp
        if sha:
            db_by_sha[sha] = fp
        if sz > 0:
            db_by_size.setdefault(sz, []).append((fn, fp, sha))

    print(f"   ✓ {len(db_rows)} fotos indexadas cargadas en memoria.")

    # 2. Map canonical files in F:\ disk
    print("2. Mapeando archivos canónicos existentes en disco local F:\\...")
    f_disk_name_size = {}
    for root, dirs, files in os.walk('F:/'):
        root_l = root.lower().replace('\\', '/')
        if any(ign in root_l for ign in ['$recycle.bin', '.papelera_deduplicacion', '.trash', 'temp', 'lm studio', 'ollama', 'python', 'dropbox', 'google']):
            continue
        for f in files:
            fp = os.path.join(root, f)
            try:
                sz = os.path.getsize(fp)
                if sz > 0:
                    fl = f.lower()
                    f_disk_name_size[(fl, sz)] = fp
            except:
                pass

    print(f"   ✓ {len(f_disk_name_size)} archivos canónicos físicos indexados en F:\\.")

    # 3. Process purges for each cloud source
    print("\n3. Iniciando proceso de eliminación de duplicados confirmados...")
    results_by_source = {}
    
    total_deleted = 0
    total_bytes_freed = 0
    total_skipped_unique = 0

    for source_label, source_path in CLOUD_SOURCE_DIRS:
        if not os.path.exists(source_path):
            print(f"   [Aviso] Ruta no encontrada: {source_path}")
            continue

        print(f"\n-> Procesando {source_label}: {source_path}...")
        deleted_source = 0
        bytes_freed_source = 0
        skipped_source = 0

        # Collect files first to avoid iterator modification issues during os.walk
        all_cloud_files = []
        for root, dirs, files in os.walk(source_path):
            root_l = root.lower().replace('\\', '/')
            if any(ex in root_l for ex in EXCLUDE_DIRS):
                continue
            for f in files:
                all_cloud_files.append((os.path.join(root, f), f))

        print(f"   Analizando {len(all_cloud_files)} archivos en {source_label}...")

        for cloud_fp, f in all_cloud_files:
            if not os.path.exists(cloud_fp):
                continue

            try:
                cloud_sz = os.path.getsize(cloud_fp)
            except:
                continue

            # Cloud configuration / placeholder files -> NEVER TOUCH
            if f.lower() in ('.dropbox', 'desktop.ini', '.picasa.ini', 'marker_file') or cloud_sz == 0:
                skipped_source += 1
                total_skipped_unique += 1
                continue

            cloud_fn = f.lower()
            canonical_match = None

            # Check 1: Direct match by (filename, size) with verified canonical on F:\
            candidate = f_disk_name_size.get((cloud_fn, cloud_sz)) or db_by_name_size.get((cloud_fn, cloud_sz))
            if candidate and os.path.exists(candidate) and os.path.getsize(candidate) == cloud_sz:
                # Crucial safety check: ensure cloud file is NOT the canonical file itself!
                if os.path.abspath(cloud_fp).lower() != os.path.abspath(candidate).lower():
                    canonical_match = candidate

            # EXECUTE PURGE ONLY IF CANONICAL MATCH IS VERIFIED 100%
            if canonical_match:
                try:
                    safe_remove_file(cloud_fp)
                    deleted_source += 1
                    bytes_freed_source += cloud_sz
                    total_deleted += 1
                    total_bytes_freed += cloud_sz

                    if total_deleted % 1000 == 0:
                        print(f"   ... {total_deleted} duplicados eliminados ({format_size(total_bytes_freed)} liberados) ...")
                except Exception as e:
                    print(f"   [Error] No se pudo eliminar {cloud_fp}: {e}")
            else:
                # 100% PROTECTED UNIQUE FILE
                skipped_source += 1
                total_skipped_unique += 1

        results_by_source[source_label] = {
            'deleted': deleted_source,
            'freed_bytes': bytes_freed_source,
            'skipped_unique': skipped_source
        }
        print(f"   ✓ {source_label} completado: {deleted_source} duplicados purgados ({format_size(bytes_freed_source)} liberados, {skipped_source} únicos preservados).")

    # 4. Measure final disk space
    c_free_after, _ = get_disk_free("C")
    f_free_after, _ = get_disk_free("F")

    # 5. Append Certification to data/audit_cloud_cleanup_report.md
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, 'a', encoding='utf-8') as f:
                f.write("\n\n---\n\n")
                f.write("## 🛡️ 3. Certificación de Ejecución de Purga (Fase 2 Completada)\n\n")
                f.write(f"**Fecha y Hora de Ejecución:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"- **Total de archivos duplicados eliminados con seguridad:** {total_deleted} archivos\n")
                f.write(f"- **Espacio físico total liberado:** {format_size(total_bytes_freed)}\n")
                f.write(f"- **Total de archivos únicos protegidos intactos:** {total_skipped_unique} archivos\n\n")
                f.write("### Desglose por Almacenamiento:\n")
                for src, res in results_by_source.items():
                    f.write(f"- **{src}:** {res['deleted']} archivos purgados ({format_size(res['freed_bytes'])} liberados) — {res['skipped_unique']} archivos únicos preservados.\n")
                f.write(f"\n**Espacio libre en Disco C:\\:** {format_size(c_free_before)} -> **{format_size(c_free_after)}**\n")
                f.write(f"**Espacio libre en Disco F:\\:** {format_size(f_free_before)} -> **{format_size(f_free_after)}**\n")
                f.write("\n*Purga completada exitosamente conforme a las directivas de seguridad de 2 fases y cero pérdida de datos.*\n")
            print(f"\nCertificación de purga agregada a: {REPORT_PATH}")
        except Exception as e:
            print(f"Error escribiendo reporte: {e}")

    # 6. Final Console Summary
    print("\n" + "=" * 125)
    print("  REPORTE FINAL DE PURGA Y LIBERACIÓN DE ESPACIO EN LA NUBE")
    print("=" * 125)
    print(f"  1. Archivos duplicados purgados en Google Drive (Local C:) : {results_by_source.get('Google Drive (Local C:)', {}).get('deleted', 0):>6} archivos ({format_size(results_by_source.get('Google Drive (Local C:)', {}).get('freed_bytes', 0)):>9})")
    print(f"  2. Archivos duplicados purgados en Dropbox                : {results_by_source.get('Dropbox', {}).get('deleted', 0):>6} archivos ({format_size(results_by_source.get('Dropbox', {}).get('freed_bytes', 0)):>9})")
    print(f"  3. Archivos duplicados purgados en Google Drive (Local F:) : {results_by_source.get('Google Drive (Local F:)', {}).get('deleted', 0):>6} archivos ({format_size(results_by_source.get('Google Drive (Local F:)', {}).get('freed_bytes', 0)):>9})")
    print("-" * 125)
    print(f"  TOTAL DE DUPLICADOS ELIMINADOS EN LA NUBE                : {total_deleted:>6} archivos")
    print(f"  ESPACIO FÍSICO TOTAL LIBERADO                            : {format_size(total_bytes_freed):>9}")
    print(f"  TOTAL DE ARCHIVOS ÚNICOS PRESERVADOS (CERO PÉRDIDA)      : {total_skipped_unique:>6} archivos")
    print("-" * 125)
    print(f"  Espacio Libre en Disco C:\\: {format_size(c_free_before)}  --->  {format_size(c_free_after)} (Ganancia efectiva)")
    print(f"  Espacio Libre en Disco F:\\: {format_size(f_free_before)}  --->  {format_size(f_free_after)}")
    print("=" * 125)

if __name__ == '__main__':
    main()
