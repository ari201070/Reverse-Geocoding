import os
import sys
import re
import json
import sqlite3
from PIL import Image

# Ensure stdout and stderr handle UTF-8 properly on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
BOOKINGS_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\apps\backend\src\data\initialBookings.json"
REPORT_OUTPUT_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\audit_anomalies_report.md"

BASE_DIR = r"F:"

BLACKLIST_DIRS = [
    '$recycle.bin', 'system volume information',
    '.papelera_deduplicacion', '.trash', 'temp'
]

# Official trip date ranges with slight buffer for travel days
TRIP_DATE_RANGES = {
    'italia_2023': ('2023-10-01', '2023-10-15', 'Viaje a Italia (Octubre 2023)'),
    'creta_2013': ('2013-07-20', '2013-08-02', 'Viaje a Creta & Bat Mitzvah (Julio 2013)'),
    'bosnia_2023': ('2023-04-28', '2023-05-08', 'Viaje a Bosnia & Balcanes (Mayo 2023)'),
    'argentina_2011': ('2011-11-01', '2011-12-05', 'Viaje a Argentina (Noviembre 2011)'),
    'argentina_2025': ('2025-09-28', '2025-10-31', 'Viaje a Argentina (Octubre 2025)'),
    'slovenia_2015': ('2015-06-30', '2015-07-10', 'Viaje a Eslovenia (Julio 2015)'),
    'denmark_2024': ('2024-09-14', '2024-09-23', 'Viaje a Dinamarca (Septiembre 2024)'),
    'croacia_montenegro_2010': ('2010-06-20', '2010-07-10', 'Viaje a Croacia y Montenegro (Junio-Julio 2010)'),
    'montenegro_2010': ('2010-06-20', '2010-07-10', 'Viaje a Croacia y Montenegro (Junio-Julio 2010)'),
    'croatia_2010': ('2010-06-20', '2010-07-10', 'Viaje a Croacia y Montenegro (Junio-Julio 2010)'),
    'chipre_2023': ('2023-08-20', '2023-09-02', 'Viaje a Chipre (Agosto 2023)')
}

MONTH_MAP = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12,
    'ינואר': 1, 'פברואר': 2, 'מרץ': 3, 'מרס': 3, 'אפריל': 4, 'מאי': 5,
    'יוני': 6, 'יולי': 7, 'אוגוסט': 8, 'ספטמבר': 9, 'אוקטובר': 10,
    'נובמבר': 11, 'דצמבר': 12
}

COMPOSITE_HEBREW_MONTHS = {
    'אפריל-מאי': [4, 5],
    'נובמבר-דצמבר': [11, 12],
    'ספטמבר-אוקטובר': [9, 10],
    'פברואר-מרץ': [2, 3]
}

def format_size(bytes_val):
    if bytes_val is None:
        return "0 KB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    return f"{bytes_val / 1024:.1f} KB"

def get_folder_year_month(folder_path):
    norm = folder_path.replace('\\', '/')
    ym = re.search(r'/(19\d\d|20\d\d)(?:/|$)', norm)
    year = int(ym.group(1)) if ym else None
    
    parts = norm.split('/')
    last_folder = parts[-1] if parts else ''
    
    # Check 01-Enero, 11-Noviembre
    nm = re.match(r'^(\d{2})[-_]', last_folder)
    if nm:
        return year, [int(nm.group(1))]
        
    for k, v in COMPOSITE_HEBREW_MONTHS.items():
        if k in last_folder:
            return year, v
            
    for k, v in MONTH_MAP.items():
        if k in last_folder.lower():
            return year, [v]
            
    return year, None

def get_core_identifier(filename):
    fn_lower = filename.lower()
    # 1. Camera photo IDs (P1070531, DSCN0959, PICT0220, etc.)
    m2 = re.search(r'(p\d{6,7}|dscn\d{3,5}|pict\d{3,5}|img_\d{3,5})', fn_lower)
    if m2:
        return m2.group(1)
    # 2. Timestamp YYYY-MM-DD HH.MM.SS
    m = re.search(r'(\d{4}-\d{2}-\d{2}[ _]\d{2}[\.:]\d{2}[\.:]\d{2})', filename)
    if m:
        return m.group(1).replace(' ', '_').replace(':', '.').lower()
    # 3. WhatsApp identifiers
    m3 = re.search(r'((?:img|vid)-\d{8}-wa\d+)', fn_lower)
    if m3:
        return m3.group(1)
    # 4. Snapedit unix timestamp
    m4 = re.search(r'snapedit_(\d{10,13})', fn_lower)
    if m4:
        return f"snapedit_{m4.group(1)}"
    return None

def extract_exif_date_direct(fp):
    try:
        with Image.open(fp) as img:
            exif = img.getexif()
            ifd = exif.get_ifd(0x8769)
            dto = ifd.get(36867) or exif.get(306)
            if dto:
                m = re.match(r'^(\d{4}):(\d{2}):(\d{2})[ T](\d{2}):(\d{2}):(\d{2})', str(dto))
                if m:
                    return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}:{m.group(6)}"
                m2 = re.match(r'^(\d{4}):(\d{2}):(\d{2})', str(dto))
                if m2:
                    return f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"
    except:
        pass
    return None

def get_dimensions(fp):
    try:
        with Image.open(fp) as img:
            return img.size # (w, h)
    except:
        return (None, None)

def main():
    print("=" * 120)
    print("  AUDITORÍA DE ANOMALÍAS, DUPLICADOS DE BAJA RESOLUCIÓN Y DESCALCES EN F:\\")
    print("  [PROTOCOLO ESTRICTO DE 2 FASES — FASE 1: SOLO LECTURA Y REPORTE]")
    print("=" * 120)

    # 1. Load DB index for fast date lookup
    db_photos = {}
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT filename, file_size, date_taken, trip_name, lat, lng FROM photos")
            for r in cursor.fetchall():
                db_photos[r['filename'].lower()] = r
            conn.close()
            print(f"Indexados {len(db_photos)} registros desde photo_catalog.db para acelerar EXIF.")
        except Exception as e:
            print(f"Advertencia: No se pudo leer DB: {e}")

    # Load initial bookings
    bookings_data = []
    if os.path.exists(BOOKINGS_PATH):
        try:
            with open(BOOKINGS_PATH, 'r', encoding='utf-8') as f:
                bookings_data = json.load(f)
            print(f"Cargados {len(bookings_data)} vouchers desde initialBookings.json.")
        except Exception as e:
            print(f"Advertencia: Error leyendo initialBookings.json: {e}")

    # Discover folders in F:\
    year_folders = [d for d in os.listdir(BASE_DIR) if re.match(r'^(19|20)\d\d$', d)]
    year_folders.sort()
    
    anomalies_by_folder = {}
    stats_by_type = {
        'ANOMALIA: DUPLICADO_COMPRIMIDO_MINIATURA': 0,
        'ANOMALIA: DUPLICADO_IDENTICO_CON_SUFIJO': 0,
        'ANOMALIA: FOTO_EN_MES_INCORRECTO': 0,
        'ANOMALIA: TAG_VIAJE_INCONGRUENTE': 0
    }

    tag_regex = re.compile(
        r'_(Italia_2023|Creta_2013|Bosnia_2023|Argentina_2011|Argentina_2025|Slovenia_2015|Denmark_2024|Croacia_Montenegro_2010|Montenegro_2010|Croatia_2010|Chipre_2023)', 
        re.IGNORECASE
    )

    print("\nIniciando escaneo exhaustivo en F:\\...")
    scanned_folders = 0
    scanned_files = 0

    for y in year_folders:
        yp = os.path.join(BASE_DIR, y)
        for root, dirs, files in os.walk(yp):
            root_lower = root.lower().replace('\\', '/')
            if any(ign in root_lower for ign in BLACKLIST_DIRS):
                continue

            media_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.mov', '.mp4'))]
            if not media_files:
                continue

            scanned_folders += 1
            scanned_files += len(media_files)
            folder_anomalies = []
            
            f_year, f_months = get_folder_year_month(root)

            # Metadata cache for current folder files to minimize disk reads
            folder_file_meta = {}
            for f in media_files:
                fp = os.path.join(root, f)
                try:
                    st = os.stat(fp)
                    sz = st.st_size
                except:
                    sz = 0

                # Lookup EXIF date
                db_r = db_photos.get(f.lower())
                ex_dt = db_r['date_taken'] if (db_r and db_r['date_taken']) else None
                if not ex_dt:
                    # check filename timestamp
                    m_fn = re.match(r'^(\d{4})-(\d{2})-(\d{2})[ _](\d{2})[\.:](\d{2})[\.:](\d{2})', f)
                    if m_fn:
                        ex_dt = f"{m_fn.group(1)}-{m_fn.group(2)}-{m_fn.group(3)} {m_fn.group(4)}:{m_fn.group(5)}:{m_fn.group(6)}"
                    else:
                        m_fn2 = re.match(r'^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', f)
                        if m_fn2:
                            ex_dt = f"{m_fn2.group(1)}-{m_fn2.group(2)}-{m_fn2.group(3)} {m_fn2.group(4)}:{m_fn2.group(5)}:{m_fn2.group(6)}"

                folder_file_meta[f] = {
                    'path': fp,
                    'size': sz,
                    'exif_date': ex_dt,
                    'dims': None # loaded on demand
                }

            # -------------------------------------------------------------
            # CRITERIO 1: Duplicados por Sufijo / Tamaño (Miniaturas vs Alta Res)
            # -------------------------------------------------------------
            core_groups = {}
            for f in media_files:
                cid = get_core_identifier(f)
                if cid:
                    core_groups.setdefault(cid, []).append(f)

            for cid, flist in core_groups.items():
                if len(flist) > 1:
                    # Load dimensions for these candidate duplicates
                    group_items = []
                    for f in flist:
                        meta = folder_file_meta[f]
                        if meta['dims'] is None:
                            meta['dims'] = get_dimensions(meta['path'])
                        group_items.append((f, meta))

                    # Find reference file with largest dimensions / size
                    group_items.sort(key=lambda x: (
                        (x[1]['dims'][0] or 0) * (x[1]['dims'][1] or 0), 
                        x[1]['size']
                    ), reverse=True)

                    best_f, best_meta = group_items[0]
                    best_area = (best_meta['dims'][0] or 0) * (best_meta['dims'][1] or 0)
                    best_sz = best_meta['size']

                    for f, meta in group_items[1:]:
                        cur_area = (meta['dims'][0] or 0) * (meta['dims'][1] or 0)
                        cur_sz = meta['size']

                        if not meta['exif_date']:
                            meta['exif_date'] = extract_exif_date_direct(meta['path'])

                        dim_str = f"{meta['dims'][0]}x{meta['dims'][1]}" if meta['dims'][0] else "N/A"
                        best_dim_str = f"{best_meta['dims'][0]}x{best_meta['dims'][1]}" if best_meta['dims'][0] else "N/A"

                        if cur_area > 0 and cur_area < 0.85 * best_area or (best_sz > 300*1024 and cur_sz < 0.65 * best_sz):
                            diag = f"ANOMALIA: DUPLICADO_COMPRIMIDO_MINIATURA | Menor tamaño/resolución vs {best_f} ({best_dim_str}, {format_size(best_sz)})"
                            stats_by_type['ANOMALIA: DUPLICADO_COMPRIMIDO_MINIATURA'] += 1
                            folder_anomalies.append({
                                'file': f,
                                'size': meta['size'],
                                'dims': dim_str,
                                'exif_date': meta['exif_date'] or "Sin EXIF",
                                'diag': diag
                            })
                        else:
                            # Same resolution/size but with duplicate counter suffix
                            if re.search(r'(\(\d+\)|_\d{1,2}|-\d{1,2}| - [Cc]opia|_copia)', f):
                                diag = f"ANOMALIA: DUPLICADO_IDENTICO_CON_SUFIJO | Gemelo idéntico por sufijo vs {best_f} ({best_dim_str}, {format_size(best_sz)})"
                                stats_by_type['ANOMALIA: DUPLICADO_IDENTICO_CON_SUFIJO'] += 1
                                folder_anomalies.append({
                                    'file': f,
                                    'size': meta['size'],
                                    'dims': dim_str,
                                    'exif_date': meta['exif_date'] or "Sin EXIF",
                                    'diag': diag
                                })

            # -------------------------------------------------------------
            # CRITERIO 2: Descalce de Fecha vs Carpeta (Ediciones tipo snapedit)
            # -------------------------------------------------------------
            for f in media_files:
                meta = folder_file_meta[f]
                f_lower = f.lower()
                m_tag = tag_regex.search(f)

                # Snapedit files special inspection
                if 'snapedit' in f_lower or 'retocado' in f_lower:
                    # Check if it has travel tag of another month or belongs to another trip
                    m_tag = tag_regex.search(f)
                    if m_tag:
                        t_key = m_tag.group(1).lower()
                        if t_key in TRIP_DATE_RANGES:
                            t_start, t_end, t_desc = TRIP_DATE_RANGES[t_key]
                            t_month = int(t_start.split('-')[1])
                            if f_months and t_month not in f_months:
                                if meta['dims'] is None:
                                    meta['dims'] = get_dimensions(meta['path'])
                                dim_str = f"{meta['dims'][0]}x{meta['dims'][1]}" if meta['dims'][0] else "N/A"
                                diag = f"ANOMALIA: FOTO_EN_MES_INCORRECTO | Edición ({t_desc}) guardada en mes {f_months} en vez de mes {t_month}"
                                stats_by_type['ANOMALIA: FOTO_EN_MES_INCORRECTO'] += 1
                                folder_anomalies.append({
                                    'file': f,
                                    'size': meta['size'],
                                    'dims': dim_str,
                                    'exif_date': meta['exif_date'] or "Sin EXIF",
                                    'diag': diag
                                })
                                continue

                # General EXIF date check vs folder
                dt = meta['exif_date']
                if not dt and ('snapedit' in f_lower or m_tag):
                    dt = extract_exif_date_direct(meta['path'])
                    meta['exif_date'] = dt

                if dt and f_months:
                    m_date = re.match(r'^(\d{4})[-:](\d{2})', dt)
                    if m_date:
                        ex_yr = int(m_date.group(1))
                        ex_mo = int(m_date.group(2))
                        # Only flag if valid year (> 1990) and clearly outside folder months
                        if ex_yr > 1990 and (ex_mo not in f_months or (f_year and abs(ex_yr - f_year) > 0)):
                            if meta['dims'] is None:
                                meta['dims'] = get_dimensions(meta['path'])
                            dim_str = f"{meta['dims'][0]}x{meta['dims'][1]}" if meta['dims'][0] else "N/A"
                            diag = f"ANOMALIA: FOTO_EN_MES_INCORRECTO | Fecha EXIF real {ex_yr}-{ex_mo:02d} no coincide con carpeta {f_year}-{f_months}"
                            stats_by_type['ANOMALIA: FOTO_EN_MES_INCORRECTO'] += 1
                            folder_anomalies.append({
                                'file': f,
                                'size': meta['size'],
                                'dims': dim_str,
                                'exif_date': dt,
                                'diag': diag
                            })

            # -------------------------------------------------------------
            # CRITERIO 3: Inconsistencia de Etiquetas de Viaje (_TagDelViaje)
            # -------------------------------------------------------------
            for f in media_files:
                m_tag = tag_regex.search(f)
                if m_tag:
                    tag_key = m_tag.group(1).lower()
                    if tag_key in TRIP_DATE_RANGES:
                        t_start, t_end, t_desc = TRIP_DATE_RANGES[tag_key]
                        meta = folder_file_meta[f]
                        dt = meta['exif_date']
                        if not dt:
                            dt = extract_exif_date_direct(meta['path'])
                            meta['exif_date'] = dt

                        if dt:
                            dt_date_part = dt.split(' ')[0].replace(':', '-')
                            if not (t_start <= dt_date_part <= t_end):
                                if meta['dims'] is None:
                                    meta['dims'] = get_dimensions(meta['path'])
                                dim_str = f"{meta['dims'][0]}x{meta['dims'][1]}" if meta['dims'][0] else "N/A"
                                diag = f"ANOMALIA: TAG_VIAJE_INCONGRUENTE | Tag _{m_tag.group(1)} en fecha {dt_date_part} fuera de ventana oficial [{t_start} a {t_end}] ({t_desc})"
                                stats_by_type['ANOMALIA: TAG_VIAJE_INCONGRUENTE'] += 1
                                folder_anomalies.append({
                                    'file': f,
                                    'size': meta['size'],
                                    'dims': dim_str,
                                    'exif_date': dt,
                                    'diag': diag
                                })

            if folder_anomalies:
                # Deduplicate entries if an item triggered both duplicate and date mismatch
                unique_anomalies = []
                seen_keys = set()
                for an in folder_anomalies:
                    k = (an['file'], an['diag'].split('|')[0].strip())
                    if k not in seen_keys:
                        seen_keys.add(k)
                        unique_anomalies.append(an)
                anomalies_by_folder[root] = unique_anomalies

    print(f"Escaneo finalizado: {scanned_files} archivos inspeccionados en {scanned_folders} carpetas.")

    # -------------------------------------------------------------
    # GENERATE MARKDOWN REPORT AND CONSOLE TABLE
    # -------------------------------------------------------------
    os.makedirs(os.path.dirname(REPORT_OUTPUT_PATH), exist_ok=True)
    md_lines = []
    md_lines.append("# INFORME DE AUDITORÍA: ANOMALÍAS, DUPLICADOS DE BAJA RESOLUCIÓN Y DESCALCES EN DISCO F:\\\n")
    md_lines.append("**Protocolo de Seguridad:** `FASE 1 (SOLO LECTURA Y REPORTE)` — Cero modificaciones en disco o DB.\n")
    md_lines.append(f"**Fecha del Análisis:** {sqlite3.datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_lines.append(f"**Total de Carpetas con Anomalías:** {len(anomalies_by_folder)}\n")
    
    total_anomalies = sum(len(v) for v in anomalies_by_folder.values())
    md_lines.append(f"**Total de Anomalías Detectadas:** {total_anomalies}\n\n")

    md_lines.append("## Resumen Ejecutivo de Anomalías por Tipo\n")
    md_lines.append("| Tipo de Anomalía | Cantidad | Descripción |")
    md_lines.append("|---|---|---|")
    md_lines.append(f"| **ANOMALIA: DUPLICADO_COMPRIMIDO_MINIATURA** | {stats_by_type['ANOMALIA: DUPLICADO_COMPRIMIDO_MINIATURA']} | Fotos con resoluciones inferiores o compresión pesada frente al original |")
    md_lines.append(f"| **ANOMALIA: DUPLICADO_IDENTICO_CON_SUFIJO** | {stats_by_type['ANOMALIA: DUPLICADO_IDENTICO_CON_SUFIJO']} | Copias redundantes idénticas diferenciadas solo por sufijos `_1`, `(1)`, etc. |")
    md_lines.append(f"| **ANOMALIA: FOTO_EN_MES_INCORRECTO** | {stats_by_type['ANOMALIA: FOTO_EN_MES_INCORRECTO']} | Fotos cuya fecha EXIF real no coincide con el mes de la carpeta física |")
    md_lines.append(f"| **ANOMALIA: TAG_VIAJE_INCONGRUENTE** | {stats_by_type['ANOMALIA: TAG_VIAJE_INCONGRUENTE']} | Etiquetas de viaje (`_Tag`) en fotos tomadas fuera del período oficial del viaje |")
    md_lines.append("\n---\n")

    md_lines.append("## Tabla Detallada de Anomalías Agrupada por Carpeta\n")

    global_index = 1
    console_sample_rows = []

    for folder, an_list in sorted(anomalies_by_folder.items()):
        md_lines.append(f"\n### 📁 Carpeta: `{folder}` ({len(an_list)} anomalías)\n")
        md_lines.append("| # | Ruta Carpeta | Nombre Archivo | Tamaño | Dimensiones (px) | Fecha Real EXIF | Tipo de Anomalía / Diagnóstico |")
        md_lines.append("|---|---|---|---|---|---|---|")

        for item in an_list:
            sz_str = format_size(item['size'])
            dims_str = item['dims']
            ex_str = item['exif_date']
            diag_str = item['diag']

            md_lines.append(f"| {global_index} | `{folder}` | `{item['file']}` | {sz_str} | {dims_str} | {ex_str} | {diag_str} |")
            
            # Keep sample for console
            if global_index <= 25 or global_index % 100 == 0:
                console_sample_rows.append((global_index, folder, item['file'], sz_str, dims_str, ex_str, diag_str))

            global_index += 1

    with open(REPORT_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))

    print(f"\nReporte completo guardado exitosamente en: {REPORT_OUTPUT_PATH}")

    # -------------------------------------------------------------
    # PRINT CONSOLE REPORT
    # -------------------------------------------------------------
    print("\n" + "=" * 135)
    print("  TABLA DETALLADA DE ANOMALÍAS ENCONTRADAS (MUESTRA REPRESENTATIVA)")
    print("=" * 135)
    print(f"| {'#':<4} | {'Ruta Carpeta':<32} | {'Nombre Archivo':<32} | {'Tamaño':<9} | {'Dims (px)':<12} | {'Fecha Real EXIF':<19} | {'Tipo de Anomalía / Diagnóstico':<45} |")
    print(f"|{'-'*6}|{'-'*34}|{'-'*34}|{'-'*11}|{'-'*14}|{'-'*21}|{'-'*47}|")

    for idx, fol, fn, sz, dm, dt, diag in console_sample_rows[:35]:
        fol_disp = fol[-32:] if len(fol) > 32 else fol
        fn_disp = fn[:30] + ".." if len(fn) > 32 else fn
        diag_disp = diag[:43] + ".." if len(diag) > 45 else diag
        print(f"| {idx:<4} | {fol_disp:<32} | {fn_disp:<32} | {sz:<9} | {dm:<12} | {dt:<19} | {diag_disp:<45} |")

    if total_anomalies > 35:
        print(f"| ...  | ... ({total_anomalies - 35} anomalías adicionales registradas en data/audit_anomalies_report.md) ...")

    print("=" * 135)
    print("\n" + "=" * 135)
    print("  RESUMEN TOTAL DE ANOMALÍAS DETECTADAS POR TIPO")
    print("=" * 135)
    print(f"  • ANOMALIA: DUPLICADO_COMPRIMIDO_MINIATURA : {stats_by_type['ANOMALIA: DUPLICADO_COMPRIMIDO_MINIATURA']:>5} archivos")
    print(f"  • ANOMALIA: DUPLICADO_IDENTICO_CON_SUFIJO   : {stats_by_type['ANOMALIA: DUPLICADO_IDENTICO_CON_SUFIJO']:>5} archivos")
    print(f"  • ANOMALIA: FOTO_EN_MES_INCORRECTO          : {stats_by_type['ANOMALIA: FOTO_EN_MES_INCORRECTO']:>5} archivos")
    print(f"  • ANOMALIA: TAG_VIAJE_INCONGRUENTE          : {stats_by_type['ANOMALIA: TAG_VIAJE_INCONGRUENTE']:>5} archivos")
    print("-" * 135)
    print(f"  TOTAL GENERAL DE ANOMALÍAS IDENTIFICADAS    : {total_anomalies:>5} archivos")
    print("=" * 135)

if __name__ == '__main__':
    main()
