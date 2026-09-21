import os
import sys
import re
import shutil
import sqlite3
import datetime

# Ensure stdout/stderr encode as UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
REPORT_ANOMALIES = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\audit_anomalies_report.md"
REPORT_PHOTOSHOP = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\audit_photoshop_garbage_report.md"

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

def normalize_folder(fol):
    fol = fol.strip('`').strip()
    if fol.startswith('F:') and not fol.startswith('F:\\'):
        fol = 'F:\\' + fol[2:].lstrip('\\')
    return fol

def resolve_target_folder(year, month):
    yp = os.path.join('F:\\', str(year))
    if not os.path.exists(yp):
        return None
    subdirs = [d for d in os.listdir(yp) if os.path.isdir(os.path.join(yp, d))]
    # 1. Match prefix e.g. 10-Octubre
    pref = f"{month:02d}-"
    for sd in subdirs:
        if sd.startswith(pref):
            return os.path.join(yp, sd)
    # 2. Match month name e.g. Octubre
    mname = MONTH_NAMES_ES[month].split('-')[1].lower()
    for sd in subdirs:
        if mname in sd.lower():
            return os.path.join(yp, sd)
    # 3. Standard fallback
    return os.path.join(yp, MONTH_NAMES_ES[month])

def main():
    print("=" * 125)
    print("  FASE 2 DE SANEAMIENTO DEFINITIVO: DEPURACIÓN DE PHOTOSHOP Y ANOMALÍAS EN F:\\")
    print("  [PROTOCOLO DE EJECUCIÓN AUTORIZADO — REGLA 1: INVIOLABILIDAD ABSOLUTA DEL ORIGINAL]")
    print("=" * 125)

    if not os.path.exists(DB_PATH):
        print(f"Error crítico: Base de datos no encontrada en {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # -------------------------------------------------------------------------
    # FASE 1: DEPURACIÓN DE RECURSOS NO-FOTOGRÁFICOS / PHOTOSHOP EN DB
    # -------------------------------------------------------------------------
    print("\n--- FASE 1: DEPURACIÓN DE RECURSOS DE PHOTOSHOP / BASURA EN DB ---")
    ps_targets = []
    if os.path.exists(REPORT_PHOTOSHOP):
        with open(REPORT_PHOTOSHOP, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('|') and not line.startswith('| #') and not line.startswith('|---') and not line.startswith('| **'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 7:
                        fol = normalize_folder(parts[2])
                        fn = parts[3].strip('`').strip()
                        ps_targets.append((fol, fn))

    print(f"Total de recursos de Photoshop/diseño listados en reporte: {len(ps_targets)}")
    
    purged_photoshop_db_count = 0
    conn.execute("BEGIN TRANSACTION")
    batch_count = 0

    for fol, fn in ps_targets:
        full_path = os.path.join(fol, fn)
        # Delete from DB
        cur = conn.execute("DELETE FROM photos WHERE file_path = ? OR (folder_source = ? AND filename = ?)", (full_path, fol, fn))
        purged_photoshop_db_count += cur.rowcount
        batch_count += 1
        if batch_count >= 1000:
            conn.commit()
            conn.execute("BEGIN TRANSACTION")
            batch_count = 0

    # Also clean any orphan Photoshop course entries by keyword in DB
    cur = conn.execute("""
        DELETE FROM photos 
        WHERE file_path LIKE '%פוטושופ%' 
           OR file_path LIKE '%עבודות פוטושופ%' 
           OR file_path LIKE '%.psd'
           OR filename LIKE '%.psd'
    """)
    purged_photoshop_db_count += cur.rowcount
    conn.commit()

    print(f"✓ Registros de Photoshop/recursos purgados de photo_catalog.db: {purged_photoshop_db_count}")

    # -------------------------------------------------------------------------
    # FASE 2: PURGA DE MINIATURAS Y DUPLICADOS REDUNDANTES EN F:\
    # -------------------------------------------------------------------------
    print("\n--- FASE 2: PURGA DE MINIATURAS Y DUPLICADOS REDUNDANTES EN DISCO ---")
    raw_duplicates = []
    if os.path.exists(REPORT_ANOMALIES):
        with open(REPORT_ANOMALIES, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('|') and not line.startswith('| #') and not line.startswith('|---') and not line.startswith('| **'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 9:
                        fol = normalize_folder(parts[2])
                        fn = parts[3].strip('`').strip()
                        diag_type = parts[7]
                        details = parts[8]

                        if 'DUPLICADO_COMPRIMIDO_MINIATURA' in diag_type or 'DUPLICADO_IDENTICO_CON_SUFIJO' in diag_type:
                            m = re.search(r'vs\s+(.*?)\s*\(\d+x\d+', details)
                            if not m:
                                m = re.search(r'vs\s+(.*?)\s*\(N/A', details)
                            orig_fn = m.group(1).strip() if m else None
                            if orig_fn:
                                raw_duplicates.append((fol, fn, orig_fn, diag_type))

    print(f"Total de parejas duplicadas parseadas para evaluación: {len(raw_duplicates)}")

    deleted_duplicates_count = 0
    bytes_freed_total = 0
    conn.execute("BEGIN TRANSACTION")
    batch_count = 0

    for fol, redundant_fn, orig_fn, diag_type in raw_duplicates:
        path_redundant = os.path.join(fol, redundant_fn)
        path_original = os.path.join(fol, orig_fn)

        # MANDATORY SAFETY CHECKS (REGLA 1: INVIOLABILIDAD DEL ORIGINAL)
        if not os.path.exists(path_redundant):
            continue
        if not os.path.exists(path_original):
            # Counterpart does not exist on disk! Never delete!
            continue
        if os.path.abspath(path_redundant) == os.path.abspath(path_original):
            # Same path! Never delete!
            continue

        size_red = os.path.getsize(path_redundant)
        size_orig = os.path.getsize(path_original)

        if size_orig <= 0:
            continue

        # Check that original is not smaller than redundant
        if size_orig < size_red:
            # Swap if original was misidentified: keep the larger one!
            path_redundant, path_original = path_original, path_redundant
            redundant_fn, orig_fn = orig_fn, redundant_fn
            size_red, size_orig = size_orig, size_red

        # REGLA 2: CERO PÉRDIDA DE EXIF / GPS
        # If redundant has GPS and original does not, copy GPS to original in DB
        cur_red = conn.execute("SELECT lat, lng, location_name, location_source, confidence_score, h3_index, date_taken FROM photos WHERE file_path = ? OR filename = ?", (path_redundant, redundant_fn)).fetchone()
        cur_orig = conn.execute("SELECT lat, lng FROM photos WHERE file_path = ? OR filename = ?", (path_original, orig_fn)).fetchone()
        
        if cur_red and cur_red['lat'] is not None and (not cur_orig or cur_orig['lat'] is None):
            conn.execute("""
                UPDATE photos 
                SET lat = ?, lng = ?, location_name = ?, location_source = ?, confidence_score = ?, h3_index = ?
                WHERE file_path = ? OR filename = ?
            """, (cur_red['lat'], cur_red['lng'], cur_red['location_name'], cur_red['location_source'], cur_red['confidence_score'], cur_red['h3_index'], path_original, orig_fn))

        # Perform physical deletion
        try:
            os.remove(path_redundant)
            deleted_duplicates_count += 1
            bytes_freed_total += size_red

            # Remove redundant entry from photo_catalog.db
            conn.execute("DELETE FROM photos WHERE file_path = ? OR (folder_source = ? AND filename = ?)", (path_redundant, fol, redundant_fn))
            batch_count += 1
            if batch_count >= 1000:
                conn.commit()
                conn.execute("BEGIN TRANSACTION")
                batch_count = 0
        except Exception as e:
            print(f"  [Aviso] No se pudo eliminar {path_redundant}: {e}")

    conn.commit()
    print(f"✓ Miniaturas y duplicados redundantes eliminados en disco: {deleted_duplicates_count} archivos")
    print(f"✓ Espacio total liberado en disco: {format_size(bytes_freed_total)}")

    # -------------------------------------------------------------------------
    # FASE 3: REUBICACIÓN DE FOTOS DESCALZADAS (SNAPEDIT Y FECHAS EN MES ERRÓNEO)
    # -------------------------------------------------------------------------
    print("\n--- FASE 3: REUBICACIÓN DE FOTOS DESCALZADAS (SNAPEDIT Y MODIFICACIONES) ---")
    mismatches = []
    if os.path.exists(REPORT_ANOMALIES):
        with open(REPORT_ANOMALIES, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('|') and not line.startswith('| #') and not line.startswith('|---') and not line.startswith('| **'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 9:
                        fol = normalize_folder(parts[2])
                        fn = parts[3].strip('`').strip()
                        dt = parts[6]
                        diag_type = parts[7]
                        details = parts[8]

                        if 'FOTO_EN_MES_INCORRECTO' in diag_type:
                            mismatches.append((fol, fn, dt, details))

    print(f"Total de archivos descalzados parseados: {len(mismatches)}")

    relocated_count = 0
    conn.execute("BEGIN TRANSACTION")
    batch_count = 0

    for fol, fn, dt, details in mismatches:
        src_path = os.path.join(fol, fn)
        if not os.path.exists(src_path):
            continue

        target_year = None
        target_month = None

        # 1. Special case: Snapedit / Italy edits in November 2023
        if '2023\\11-Noviembre' in fol or '2023/11-Noviembre' in fol:
            if 'snapedit' in fn.lower() or 'pisa' in fn.lower() or 'cattedrale' in fn.lower() or 'italia' in fn.lower():
                target_year = 2023
                target_month = 10

        # 2. Extract from EXIF date or details
        if not target_month and dt and dt != 'Sin EXIF':
            m_dt = re.match(r'^(\d{4})[-:](\d{2})', dt)
            if m_dt:
                target_year = int(m_dt.group(1))
                target_month = int(m_dt.group(2))

        if not target_month:
            m_det = re.search(r'Fecha EXIF real\s+(\d{4})-(\d{2})', details)
            if m_det:
                target_year = int(m_det.group(1))
                target_month = int(m_det.group(2))

        if not (target_year and target_month and 1 <= target_month <= 12 and target_year > 1990):
            continue

        target_folder = resolve_target_folder(target_year, target_month)
        if not target_folder:
            continue

        if os.path.abspath(fol).lower() == os.path.abspath(target_folder).lower():
            continue

        os.makedirs(target_folder, exist_ok=True)
        dst_path = os.path.join(target_folder, fn)

        if os.path.exists(dst_path):
            # Destination already exists: compare size
            if os.path.getsize(src_path) == os.path.getsize(dst_path):
                # Exact copy already in target folder: remove source
                try:
                    os.remove(src_path)
                    relocated_count += 1
                except:
                    pass
                continue
            else:
                # Name collision with different size: rename with original date prefix
                base_name, ext = os.path.splitext(fn)
                clean_dt = dt.replace(':', '').replace(' ', '_') if dt and dt != 'Sin EXIF' else f"{target_year}{target_month:02d}"
                new_fn = f"{clean_dt}_{base_name}{ext}"
                dst_path = os.path.join(target_folder, new_fn)

        try:
            shutil.move(src_path, dst_path)
            relocated_count += 1

            # Update DB path
            conn.execute("""
                UPDATE photos 
                SET file_path = ?, folder_source = ?, filename = ? 
                WHERE file_path = ? OR (folder_source = ? AND filename = ?)
            """, (dst_path, target_folder, os.path.basename(dst_path), src_path, fol, fn))

            batch_count += 1
            if batch_count >= 1000:
                conn.commit()
                conn.execute("BEGIN TRANSACTION")
                batch_count = 0
        except Exception as e:
            print(f"  [Aviso] Error al reubicar {fn}: {e}")

    conn.commit()
    print(f"✓ Total de fotos descalzadas reubicadas en su carpeta correcta: {relocated_count} archivos")

    # -------------------------------------------------------------------------
    # FASE 4: REPORTE FINAL DE CONSOLIDACIÓN
    # -------------------------------------------------------------------------
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM photos")
    total_db_photos = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM photos WHERE lat IS NOT NULL AND lat != 0")
    total_with_gps = cursor.fetchone()[0]

    cursor.execute("""
        SELECT location_source, count(*) 
        FROM photos 
        GROUP BY location_source 
        ORDER BY count(*) DESC
    """)
    sources_breakdown = cursor.fetchall()

    conn.close()

    print("\n" + "=" * 125)
    print("  REPORTE FINAL DE CONSOLIDACIÓN Y SANEAMIENTO")
    print("=" * 125)
    print(f"  1. Recursos de Photoshop purgados de la DB : {purged_photoshop_db_count:>6} registros")
    print(f"  2. Miniaturas y duplicados eliminados en F: : {deleted_duplicates_count:>6} archivos físicos")
    print(f"  3. Espacio total liberado en disco F:\\     : {format_size(bytes_freed_total):>9}")
    print(f"  4. Fotos descalzadas reubicadas con éxito  : {relocated_count:>6} archivos")
    print("-" * 125)
    print(f"  TOTAL DE FOTOS ÚNICAS Y LIMPIAS EN DB      : {total_db_photos:>6} archivos")
    print(f"  • Fotos con geolocalización activa (GPS)   : {total_with_gps:>6} ({total_with_gps / total_db_photos * 100:.2f}%)")
    print(f"  • Fotos pendientes de geolocalizar         : {total_db_photos - total_with_gps:>6} ({(total_db_photos - total_with_gps) / total_db_photos * 100:.2f}%)")
    print("\n  Distribución actual por Fuente de Ubicación en Catálogo Único:")
    for src, cnt in sources_breakdown:
        src_label = src if src else 'SIN_GEO (Pendiente)'
        pct = (cnt / total_db_photos) * 100
        print(f"    • {src_label:<32}: {cnt:>5} fotos ({pct:5.2f}%)")
    print("=" * 125)

if __name__ == '__main__':
    main()
