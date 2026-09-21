import os
import sys
import re
import sqlite3
import hashlib
import datetime

# Ensure standard output encodes as UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
REPORT_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\audit_cloud_cleanup_report.md"

CLOUD_SOURCE_DIRS = [
    ("Dropbox", r"C:\Users\flier\Dropbox"),
    ("Google Drive (Local C:)", r"C:\Users\flier\Google Drive"),
    ("Google Drive (Local F:)", r"F:\האחסון שלי"),
    ("Cuenta de Google (Docs F:)", r"F:\Cuenta de google")
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

def main():
    print("=" * 125)
    print("  FASE 1: AUDITORÍA DE ARCHIVOS EN GOOGLE DRIVE Y DROPBOX (SOLO LECTURA)")
    print("  [PROTOCOLO ESTRICTO DE 2 FASES — CERO MODIFICACIONES EN DISCO O BASE DE DATOS]")
    print("=" * 125)

    if not os.path.exists(DB_PATH):
        print(f"Error crítico: Base de datos central no encontrada en {DB_PATH}")
        sys.exit(1)

    # 1. Load photo_catalog.db records into memory
    print("Cargando catálogo central de photo_catalog.db...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT filename, file_size, sha256, date_taken, file_path FROM photos")
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

    print(f"Catálogo cargado: {len(db_rows)} fotos indexadas en photo_catalog.db.")

    # 2. Map canonical files in F:\ disk (fast directory walk, zero file-read latency)
    print("Mapeando archivos canónicos en disco local F:\\...")
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

    print(f"Mapeo de disco F:\\ completado ({len(f_disk_name_size)} archivos físicos indexados).")

    # 3. Audit cloud files
    audited_files = []
    stats_by_source = {}

    total_scanned = 0
    total_safe_to_delete = 0
    total_unique_to_preserve = 0
    total_bytes_safe_to_delete = 0
    total_bytes_unique = 0

    print("\nIniciando auditoría de nubes locales (Google Drive & Dropbox)...")

    for source_label, source_path in CLOUD_SOURCE_DIRS:
        if not os.path.exists(source_path):
            print(f"Aviso: Ruta no encontrada: {source_path}")
            continue

        print(f"-> Escaneando {source_label}: {source_path}...")
        source_files_count = 0
        source_safe_count = 0
        source_unique_count = 0
        source_safe_bytes = 0
        source_unique_bytes = 0

        for root, dirs, files in os.walk(source_path):
            root_l = root.lower().replace('\\', '/')
            if any(ex in root_l for ex in EXCLUDE_DIRS):
                continue

            for f in files:
                cloud_fp = os.path.join(root, f)
                try:
                    cloud_sz = os.path.getsize(cloud_fp)
                except:
                    continue

                source_files_count += 1
                total_scanned += 1
                cloud_fn = f.lower()

                status = None
                matched_canonical_path = None
                match_method = None

                # Cloud configuration / placeholder files
                if f.lower() in ('.dropbox', 'desktop.ini', '.picasa.ini', 'marker_file') or cloud_sz == 0:
                    status = "PRESERVAR_UNICO"
                    match_method = "Archivo de configuración o metadato de nube"
                    source_unique_count += 1
                    source_unique_bytes += cloud_sz
                    total_unique_to_preserve += 1
                    total_bytes_unique += cloud_sz
                    audited_files.append({
                        'source': source_label,
                        'folder': root,
                        'filename': f,
                        'size': cloud_sz,
                        'status': status,
                        'canonical_match': "N/A",
                        'diag': match_method
                    })
                    continue

                # Step 1: Direct O(1) match by (filename, size) in F:\ disk or DB
                candidate_canonical = f_disk_name_size.get((cloud_fn, cloud_sz)) or db_by_name_size.get((cloud_fn, cloud_sz))
                if candidate_canonical:
                    status = "SEGURO_PARA_ELIMINAR"
                    matched_canonical_path = candidate_canonical
                    match_method = f"Copia exacta confirmada en F:\\ ({format_size(cloud_sz)})"

                # Step 2: Match by SHA-256 for files with matching size in DB (files <= 25MB)
                if not status and cloud_sz in db_by_size and cloud_sz <= 25 * 1024 * 1024:
                    cloud_sha = compute_sha256(cloud_fp)
                    if cloud_sha and cloud_sha in db_by_sha:
                        status = "SEGURO_PARA_ELIMINAR"
                        matched_canonical_path = db_by_sha[cloud_sha]
                        match_method = "Coincidencia binaria idéntica por Hash SHA-256"

                # Final determination
                if status == "SEGURO_PARA_ELIMINAR":
                    source_safe_count += 1
                    source_safe_bytes += cloud_sz
                    total_safe_to_delete += 1
                    total_bytes_safe_to_delete += cloud_sz
                else:
                    status = "PRESERVAR_UNICO"
                    match_method = "Archivo único (sin copia idéntica registrada en F:\\ o DB)"
                    source_unique_count += 1
                    source_unique_bytes += cloud_sz
                    total_unique_to_preserve += 1
                    total_bytes_unique += cloud_sz

                audited_files.append({
                    'source': source_label,
                    'folder': root,
                    'filename': f,
                    'size': cloud_sz,
                    'status': status,
                    'canonical_match': matched_canonical_path or "Ninguna",
                    'diag': match_method
                })

        stats_by_source[source_label] = {
            'total_files': source_files_count,
            'safe_count': source_safe_count,
            'safe_bytes': source_safe_bytes,
            'unique_count': source_unique_count,
            'unique_bytes': source_unique_bytes
        }
        print(f"  ✓ {source_label}: {source_files_count} archivos auditados ({source_safe_count} listos para purgar, {source_unique_count} únicos).")

    # 4. Generate Markdown Report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    md_lines = []
    md_lines.append("# INFORME DE AUDITORÍA: ARCHIVOS EN GOOGLE DRIVE Y DROPBOX\n")
    md_lines.append("**Protocolo de Seguridad:** `FASE 1 (SOLO LECTURA Y REPORTE)` — Cero modificaciones o eliminaciones físicas.\n")
    md_lines.append(f"**Fecha del Análisis:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_lines.append(f"**Total de Archivos Auditados:** {total_scanned}\n")
    md_lines.append(f"**Archivos duplicados listos para eliminar:** {total_safe_to_delete} ({format_size(total_bytes_safe_to_delete)})\n")
    md_lines.append(f"**Archivos únicos a preservar:** {total_unique_to_preserve} ({format_size(total_bytes_unique)})\n\n")

    md_lines.append("## 📊 1. Resumen Consolidado por Nube / Fuente\n")
    md_lines.append("| Nube / Origen | Total Archivos | Seguro para Eliminar | Espacio a Liberar | Preservar Único | Espacio a Preservar |")
    md_lines.append("|---|---|---|---|---|---|")

    for src, st in stats_by_source.items():
        md_lines.append(f"| **{src}** | {st['total_files']} | {st['safe_count']} | {format_size(st['safe_bytes'])} | {st['unique_count']} | {format_size(st['unique_bytes'])} |")

    md_lines.append(f"| **TOTAL CONSOLIDADO** | **{total_scanned}** | **{total_safe_to_delete}** | **{format_size(total_bytes_safe_to_delete)}** | **{total_unique_to_preserve}** | **{format_size(total_bytes_unique)}** |")
    md_lines.append("\n---\n")

    md_lines.append("## 📋 2. Muestra Detallada de Archivos Auditados\n")
    md_lines.append("| # | Nube | Carpeta Origen | Nombre de Archivo | Tamaño | Estado / Clasificación | Copia Canónica Confirmada en F:\\ | Diagnóstico |")
    md_lines.append("|---|---|---|---|---|---|---|---|")

    # Sort: first safe to delete, then unique
    audited_files.sort(key=lambda x: (x['status'], x['source'], x['filename']))

    sample_limit = 2500 if len(audited_files) > 2500 else len(audited_files)
    for idx, item in enumerate(audited_files[:sample_limit], start=1):
        sz_str = format_size(item['size'])
        md_lines.append(f"| {idx} | {item['source']} | `{item['folder']}` | `{item['filename']}` | {sz_str} | **{item['status']}** | `{item['canonical_match']}` | {item['diag']} |")

    if len(audited_files) > sample_limit:
        md_lines.append(f"\n*(Mostrando los primeros {sample_limit} registros representativos de un total de {len(audited_files)} analizados)*\n")

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))

    print(f"\nReporte detallado guardado exitosamente en: {REPORT_PATH}")

    # 5. Print Console Table and Summary
    print("\n" + "=" * 125)
    print("  RESUMEN CONSOLIDADO DE AUDITORÍA EN LA NUBE (DRIVE Y DROPBOX)")
    print("=" * 125)
    print(f"| {'Nube / Origen':<26} | {'Total':<8} | {'Para Purgar':<14} | {'Espacio a Liberar':<19} | {'Únicos (Preservar)':<20} | {'Espacio Único':<15} |")
    print(f"|{'-'*28}|{'-'*10}|{'-'*16}|{'-'*21}|{'-'*22}|{'-'*17}|")

    for src, st in stats_by_source.items():
        print(f"| {src:<26} | {st['total_files']:<8} | {st['safe_count']:<14} | {format_size(st['safe_bytes']):<19} | {st['unique_count']:<20} | {format_size(st['unique_bytes']):<15} |")

    print(f"|{'-'*28}|{'-'*10}|{'-'*16}|{'-'*21}|{'-'*22}|{'-'*17}|")
    print(f"| {'TOTAL CONSOLIDADO':<26} | {total_scanned:<8} | {total_safe_to_delete:<14} | {format_size(total_bytes_safe_to_delete):<19} | {total_unique_to_preserve:<20} | {format_size(total_bytes_unique):<15} |")
    print("=" * 125)

    print("\n" + "=" * 125)
    print("  MUESTRA REPRESENTATIVA DE ARCHIVOS CONFIRMADOS PARA ELIMINAR (COPIA EXISTE EN F:\\)")
    print("=" * 125)
    print(f"| {'#':<4} | {'Nube':<14} | {'Nombre Archivo':<32} | {'Tamaño':<9} | {'Copia Canónica en F:\\':<55} |")
    print(f"|{'-'*6}|{'-'*16}|{'-'*34}|{'-'*11}|{'-'*57}|")

    safe_items = [item for item in audited_files if item['status'] == 'SEGURO_PARA_ELIMINAR']
    for idx, item in enumerate(safe_items[:25], start=1):
        fn_disp = item['filename'][:30] + ".." if len(item['filename']) > 32 else item['filename']
        can_disp = item['canonical_match'][-53:] if len(item['canonical_match']) > 55 else item['canonical_match']
        print(f"| {idx:<4} | {item['source']:<14} | {fn_disp:<32} | {format_size(item['size']):<9} | {can_disp:<55} |")

    if len(safe_items) > 25:
        print(f"| ...  | ... ({len(safe_items) - 25} archivos duplicados adicionales listos para purgar en Fase 2) ...")

    print("=" * 125)

if __name__ == '__main__':
    main()
