import os
import sys
import re
import sqlite3
import datetime
from PIL import Image

# Ensure standard output encodes as UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
BASE_DIR = r"F:"
REPORT_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\audit_photoshop_garbage_report.md"

# Exclusions: recycle bins, system directories, installed applications
EXCLUDE_DIRS = [
    '$recycle.bin', 'system volume information',
    '.papelera_deduplicacion', '.trash', 'temp',
    'lm studio', 'ollama', 'python'
]

# Patterns
PHOTOSHOP_KEYWORDS = [
    'photoshop', 'פוטושופ', 'עבודות פוטושופ', 'curso', 'ejercicio', 'tutorial',
    'brush', 'pincel', 'texture', 'textura', 'layer', 'capa', 'blendmodes',
    'smart_objects', 'gradients', 'filter_blur'
]
PHOTOSHOP_REGEX = re.compile(r'(' + '|'.join(PHOTOSHOP_KEYWORDS) + r')', re.IGNORECASE)

SCREENSHOT_REGEX = re.compile(r'(screenshot|captura|pantallazo|screen_shot|screen-shot)', re.IGNORECASE)

GRAPHICS_KEYWORDS = ['logo', 'icon', 'icono', 'banner', 'clipart', 'mockup', 'flyer', 'plantilla', 'template', 'vector']
GRAPHICS_REGEX = re.compile(r'(?:^|[\W_])(' + '|'.join(GRAPHICS_KEYWORDS) + r')(?:$|[\W_])', re.IGNORECASE)

DESIGN_EXTENSIONS = ('.psd', '.ai', '.eps', '.svg')

def format_size(bytes_val):
    if bytes_val is None:
        return "0 KB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    return f"{bytes_val / 1024:.1f} KB"

def extract_exif_metadata(fp):
    """
    Extracts Make, Model, and Software from EXIF if available.
    Returns (camera_str, software_str, has_hardware_camera)
    """
    try:
        with Image.open(fp) as img:
            exif = img.getexif()
            if not exif:
                return "Sin EXIF", None, False
            make = exif.get(271)
            model = exif.get(272)
            software = exif.get(305)
            
            make_str = str(make).strip() if make else ""
            model_str = str(model).strip() if model else ""
            soft_str = str(software).strip() if software else None
            
            has_camera = bool(make_str or model_str)
            if has_camera:
                cam = f"{make_str} {model_str}".strip()
            else:
                cam = "Sin Cámara (Vacío)"
            return cam, soft_str, has_camera
    except:
        return "No legible / N/A", None, False

def main():
    print("=" * 125)
    print("  AUDITORÍA DE ARCHIVOS NO-FOTOGRÁFICOS / CURSO DE PHOTOSHOP EN DISCO F:\\ Y DB")
    print("  [PROTOCOLO ESTRICTO DE 2 FASES — FASE 1: SOLO LECTURA Y REPORTE]")
    print("=" * 125)

    # 1. Index DB records for cross-referencing
    db_items = {}
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT id, file_path, filename, file_size FROM photos")
            for r in cursor.fetchall():
                db_items[r['filename'].lower()] = r
            conn.close()
            print(f"Base de datos central photo_catalog.db indexada ({len(db_items)} registros).")
        except Exception as e:
            print(f"Advertencia: Error al leer DB: {e}")

    # 2. Walk F:\ excluding software and trash
    print("Iniciando escaneo de directorios en disco F:\\...")
    detected_assets = []
    seen_paths = set()
    
    total_files_scanned = 0

    for root, dirs, files in os.walk(BASE_DIR):
        root_norm = root.replace('\\', '/')
        root_lower = root_norm.lower()
        if any(ex in root_lower for ex in EXCLUDE_DIRS):
            continue

        for f in files:
            fp = os.path.join(root, f)
            fl = f.lower()
            total_files_scanned += 1
            
            try:
                st = os.stat(fp)
                sz = st.st_size
            except:
                sz = 0

            # Classification rules
            is_psd_ext = fl.endswith(DESIGN_EXTENSIONS)
            is_photoshop_kw = bool(PHOTOSHOP_REGEX.search(fl) or PHOTOSHOP_REGEX.search(root_lower))
            is_screenshot = bool(SCREENSHOT_REGEX.search(fl))
            is_graphics = bool(GRAPHICS_REGEX.search(fl))

            category = None
            diag = None

            if is_psd_ext:
                category = "ARCHIVO_DISENO_PSD"
                diag = f"Extensión de archivo de diseño de capas ({os.path.splitext(f)[1].upper()})"
            elif is_photoshop_kw:
                category = "RECURSO_CURSO_PHOTOSHOP"
                match_kw = PHOTOSHOP_REGEX.search(fl) or PHOTOSHOP_REGEX.search(root_lower)
                kw_found = match_kw.group(0) if match_kw else "photoshop"
                diag = f"Recurso/ejercicio de curso de diseño (Palabra clave: '{kw_found}')"
            elif is_screenshot:
                category = "CAPTURA_DE_PANTALLA"
                diag = "Captura de pantalla de dispositivo móvil o interfaz de PC"
            elif is_graphics:
                category = "GRAFICO_LOGO_STOCK"
                match_gw = GRAPHICS_REGEX.search(fl)
                gw_found = match_gw.group(0) if match_gw else "logo"
                diag = f"Elemento gráfico vectorial, ícono o logo de empresa ('{gw_found}')"

            if category:
                # Check camera metadata
                cam_info, soft_info, has_cam = extract_exif_metadata(fp)
                if soft_info and "photoshop" in soft_info.lower() and not has_cam:
                    diag += f" | Software: {soft_info}"

                in_db = f.lower() in db_items
                seen_paths.add(fp.lower())

                detected_assets.append({
                    'path': fp,
                    'filename': f,
                    'folder': root,
                    'size': sz,
                    'category': category,
                    'camera': cam_info,
                    'software': soft_info,
                    'diag': diag,
                    'in_db': in_db
                })

    # 3. Check for any DB records pointing to Photoshop / course files that might not have been walked
    db_additional = 0
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT id, file_path, filename, file_size FROM photos")
            for r in cursor.fetchall():
                fp = r['file_path'] or ""
                fn = r['filename'] or ""
                fpl = fp.lower()
                fnl = fn.lower()
                
                if fp.lower() in seen_paths:
                    continue
                    
                cat = None
                diag = None
                if fnl.endswith(DESIGN_EXTENSIONS) or fpl.endswith(DESIGN_EXTENSIONS):
                    cat = "ARCHIVO_DISENO_PSD"
                    diag = "Archivo de capas PSD registrado en catálogo DB"
                elif any(k in fpl for k in ['פוטושופ', 'photoshop', 'עבודות פוטושופ']) or any(k in fnl for k in ['photoshop', 'פוטושופ']):
                    cat = "RECURSO_CURSO_PHOTOSHOP"
                    diag = "Registro en DB ubicado en ruta de curso de Photoshop"
                elif 'screenshot' in fnl or 'captura' in fnl or 'pantallazo' in fnl:
                    cat = "CAPTURA_DE_PANTALLA"
                    diag = "Captura de pantalla registrada en catálogo DB"
                elif any(k in fnl for k in ['logo', 'icon', 'banner', 'clipart']):
                    cat = "GRAFICO_LOGO_STOCK"
                    diag = "Gráfico o logo registrado en catálogo DB"

                if cat:
                    db_additional += 1
                    seen_paths.add(fp.lower())
                    sz = r['file_size'] or 0
                    cam_info = "Sin Cámara (Vacío)"
                    if os.path.exists(fp):
                        cam_info, soft_info, _ = extract_exif_metadata(fp)
                    detected_assets.append({
                        'path': fp,
                        'filename': fn,
                        'folder': os.path.dirname(fp),
                        'size': sz,
                        'category': cat,
                        'camera': cam_info,
                        'software': None,
                        'diag': diag,
                        'in_db': True
                    })
            conn.close()
        except Exception as e:
            print(f"Error revisando DB extra: {e}")

    print(f"Escaneo completado: {total_files_scanned} archivos revisados.")
    print(f"Total de recursos no-fotográficos detectados: {len(detected_assets)}.")

    # 4. Group by category and compute stats
    stats_by_cat = {}
    for item in detected_assets:
        cat = item['category']
        if cat not in stats_by_cat:
            stats_by_cat[cat] = {'count': 0, 'size': 0, 'in_db': 0}
        stats_by_cat[cat]['count'] += 1
        stats_by_cat[cat]['size'] += item['size']
        if item['in_db']:
            stats_by_cat[cat]['in_db'] += 1

    total_size_bytes = sum(item['size'] for item in detected_assets)
    total_in_db = sum(1 for item in detected_assets if item['in_db'])

    # 5. Generate Markdown Report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    md_lines = []
    md_lines.append("# INFORME DE AUDITORÍA: ARCHIVOS NO-FOTOGRÁFICOS Y RECURSOS DE CURSO DE PHOTOSHOP\n")
    md_lines.append("**Protocolo de Seguridad:** `FASE 1 (SOLO LECTURA Y REPORTE)` — Cero modificaciones o eliminaciones físicas en disco.\n")
    md_lines.append(f"**Fecha del Análisis:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_lines.append(f"**Archivos no-fotográficos detectados:** {len(detected_assets)} archivos\n")
    md_lines.append(f"**Espacio total ocupado estimado:** {format_size(total_size_bytes)}\n")
    md_lines.append(f"**Archivos indexados en `photo_catalog.db` que deben ser desindexados:** {total_in_db}\n\n")

    md_lines.append("## 📊 Resumen Consolidado por Categoría\n")
    md_lines.append("| Categoría de Recurso | Cantidad Archivos | Espacio en Disco | Presentes en DB | Descripción |")
    md_lines.append("|---|---|---|---|---|")
    
    cat_names = {
        'RECURSO_CURSO_PHOTOSHOP': 'Recursos de Curso de Photoshop',
        'ARCHIVO_DISENO_PSD': 'Archivos de Capas PSD / Diseño',
        'CAPTURA_DE_PANTALLA': 'Capturas de Pantalla (Screenshots)',
        'GRAFICO_LOGO_STOCK': 'Gráficos, Logos e Íconos'
    }

    for cat_code, info in sorted(stats_by_cat.items(), key=lambda x: -x[1]['count']):
        c_label = cat_names.get(cat_code, cat_code)
        md_lines.append(f"| **{c_label}** | {info['count']} | {format_size(info['size'])} | {info['in_db']} | {cat_code} |")

    md_lines.append(f"| **TOTAL CONSOLIDADO** | **{len(detected_assets)}** | **{format_size(total_size_bytes)}** | **{total_in_db}** | |")
    md_lines.append("\n---\n")

    md_lines.append("## 📋 Tabla Detallada de Archivos Clasificados\n")
    md_lines.append("| # | Ruta Completa | Nombre de Archivo | Tamaño | Cámara EXIF | Diagnóstico / Motivo de Clasificación |")
    md_lines.append("|---|---|---|---|---|---|")

    # Sort detected assets by category and path
    detected_assets.sort(key=lambda x: (x['category'], x['folder'], x['filename']))

    for idx, item in enumerate(detected_assets, start=1):
        sz_str = format_size(item['size'])
        cam_str = item['camera']
        diag_str = item['diag']
        if item['in_db']:
            diag_str = "[EN DB] " + diag_str

        md_lines.append(f"| {idx} | `{item['folder']}` | `{item['filename']}` | {sz_str} | {cam_str} | {diag_str} |")

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))

    print(f"\nReporte detallado guardado exitosamente en: {REPORT_PATH}")

    # 6. Print Console Table Sample and Summary
    print("\n" + "=" * 125)
    print("  RESUMEN GENERAL DE ARCHIVOS NO-FOTOGRÁFICOS / PHOTOSHOP DETECTADOS")
    print("=" * 125)
    for cat_code, info in sorted(stats_by_cat.items(), key=lambda x: -x[1]['count']):
        c_label = cat_names.get(cat_code, cat_code)
        print(f"  • {c_label:<38}: {info['count']:>4} archivos ({format_size(info['size']):>9}) [En DB: {info['in_db']}]")
    print("-" * 125)
    print(f"  TOTAL DE ACTIVOS NO-FOTOGRÁFICOS IDENTIFICADOS : {len(detected_assets):>4} archivos ({format_size(total_size_bytes)})")
    print("=" * 125)

    print("\n" + "=" * 125)
    print("  MUESTRA REPRESENTATIVA DE LA TABLA DE AUDITORÍA")
    print("=" * 125)
    print(f"| {'#':<4} | {'Nombre Archivo':<35} | {'Tamaño':<9} | {'Cámara EXIF':<22} | {'Diagnóstico / Clasificación':<45} |")
    print(f"|{'-'*6}|{'-'*37}|{'-'*11}|{'-'*24}|{'-'*47}|")

    sample_items = detected_assets[:15] + detected_assets[len(detected_assets)//2:len(detected_assets)//2 + 5] + detected_assets[-10:]
    for s_idx, item in enumerate(sample_items, start=1):
        fn_disp = item['filename'][:33] + ".." if len(item['filename']) > 35 else item['filename']
        cam_disp = item['camera'][:20] + ".." if len(item['camera']) > 22 else item['camera']
        diag_disp = item['diag'][:43] + ".." if len(item['diag']) > 45 else item['diag']
        print(f"| {s_idx:<4} | {fn_disp:<35} | {format_size(item['size']):<9} | {cam_disp:<22} | {diag_disp:<45} |")

    print(f"\n[Ver la lista completa de {len(detected_assets)} registros en {REPORT_PATH}]")
    print("=" * 125)

if __name__ == '__main__':
    main()
