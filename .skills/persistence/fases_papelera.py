#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 0: Consolidacion de Papeleras + Clasificacion de Fotos en Disco F:
Modo: DRY RUN por defecto. Pasa --execute para aplicar cambios reales.
"""
import os, sys, shutil, hashlib, json, sqlite3, re, io
from pathlib import Path
from datetime import datetime
from collections import defaultdict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════
DRY_RUN = "--execute" not in sys.argv
DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ORPHAN_TRASH = Path("F:/.Papelera_Deduplicacion")
ROOT = Path("F:/")

MONTH_MAP = {
    "Enero": "01-Enero", "Febrero": "02-Febrero", "Marzo": "03-Marzo",
    "Abril": "04-Abril", "Mayo": "05-Mayo", "Junio": "06-Junio",
    "Julio": "07-Julio", "Agosto": "08-Agosto", "Septiembre": "09-Septiembre",
    "Octubre": "10-Octubre", "Noviembre": "11-Noviembre", "Diciembre": "12-Diciembre",
}
MONTH_NAME_TO_NUM = {v.split("-")[1]: v.split("-")[0] for v in MONTH_MAP.values()}

PROTECTED_ZONES = [
    "F:/copia de los datos de Google",
    "F:/גברים רעבים באיטליה-2023",
    "F:/טיול לארגנטינה",
]

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".tiff", ".tif", ".bmp", ".gif", ".raw", ".cr2", ".nef", ".arw", ".dng"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".3gp", ".wmv"}
MEDIA_EXTS = PHOTO_EXTS | VIDEO_EXTS

# ════════════════════════════════════════════════════════════════
# UTILIDADES
# ════════════════════════════════════════════════════════════════
def file_hash(path, block=65536):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(block)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None

def is_protected(path_str):
    for z in PROTECTED_ZONES:
        if path_str.lower().startswith(z.lower()):
            return True
    return False

def extract_year_month_from_path(path_str):
    r"""Extrae anio y mes de una ruta tipo F:\.Papelera_Deduplicacion\2015\Julio\..."""
    parts = Path(path_str).parts
    year, month = None, None
    for i, p in enumerate(parts):
        if p.isdigit() and len(p) == 4 and 2000 <= int(p) <= 2030:
            year = int(p)
            if i + 1 < len(parts):
                candidate = parts[i + 1]
                if candidate in MONTH_MAP:
                    month = candidate
            break
    return year, month

def get_month_folder_name(month_name):
    return MONTH_MAP.get(month_name, None)

def get_photo_datetime(path_str):
    """Lee DateTimeOriginal del EXIF via piexif o fallback a mtime."""
    try:
        import piexif
        from piexif import ImageIFD
        exif_dict = piexif.load(path_str)
        raw = exif_dict.get("Exif", {}).get(ImageIFD.DateTimeOriginal)
        if raw:
            return raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else str(raw)
    except Exception:
        pass
    try:
        dt = os.path.getmtime(path_str)
        return datetime.fromtimestamp(dt).strftime("%Y:%m:%d %H:%M:%S")
    except Exception:
        return None

def classify_media_file(filepath):
    """Determina año y MM-NombreMes de un archivo multimedia basándose en EXIF/mtime."""
    ext = filepath.suffix.lower()
    if ext not in MEDIA_EXTS:
        return None, None

    exif_dt = get_photo_datetime(str(filepath))
    if exif_dt:
        # Formato EXIF: "2025:10:05 14:30:00"
        m = re.match(r"(\d{4}):(\d{2}):(\d{2})", exif_dt)
        if m:
            year = int(m.group(1))
            month_num = int(m.group(2))
            month_names = list(MONTH_MAP.keys())
            if 1 <= month_num <= 12:
                return year, f"{month_num:02d}-{month_names[month_num - 1]}"

    # Fallback: mtime
    try:
        dt = datetime.fromtimestamp(os.path.getmtime(filepath))
        month_names = list(MONTH_MAP.keys())
        return dt.year, f"{dt.month:02d}-{month_names[dt.month - 1]}"
    except Exception:
        return None, None

# ════════════════════════════════════════════════════════════════
# FASE 0: CONSOLIDACIÓN DE PAPELERAS
# ════════════════════════════════════════════════════════════════
def phase0_consolidate_trash():
    print("\n" + "=" * 60)
    print("  FASE 0: Consolidación de Papeleras de Deduplicación")
    print("=" * 60)

    if not ORPHAN_TRASH.exists():
        print("  [OK] No existe carpeta orphana. Nada que consolidar.")
        return 0, 0

    stats = {"migrated": 0, "removed_dup": 0, "skipped_no_year": 0, "errors": 0}
    year_dirs = []
    other_dirs = []

    for item in ORPHAN_TRASH.iterdir():
        if item.is_dir():
            if item.name.isdigit() and len(item.name) == 4 and 2000 <= int(item.name) <= 2030:
                year_dirs.append(item)
            else:
                other_dirs.append(item)

    # --- Migrar carpetas con año ---
    for ydir in sorted(year_dirs):
        year = int(ydir.name)
        dest_trash_base = ROOT / f".Papelera_Deduplicacion{year}"

        for month_dir in sorted(ydir.iterdir()):
            if not month_dir.is_dir():
                # Archivo suelto en nivel de año → mover a papelera raíz del año
                dest_file = dest_trash_base / month_dir.name
                if dest_file.exists():
                    if file_hash(str(month_dir)) == file_hash(str(dest_file)):
                        if not DRY_RUN:
                            os.remove(str(month_dir))
                        stats["removed_dup"] += 1
                        print(f"  [DEL-DUP] {month_dir.name} (ya existe en papelera {year})")
                    else:
                        if not DRY_RUN:
                            os.remove(str(month_dir))
                        stats["removed_dup"] += 1
                        print(f"  [DEL-DUP] {month_dir.name} (hash difiere, descartado)")
                else:
                    if not DRY_RUN:
                        dest_trash_base.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(month_dir), str(dest_file))
                    stats["migrated"] += 1
                continue

            month_name = month_dir.name
            if month_name not in MONTH_MAP:
                print(f"  [SKIP] Mes no reconocido: {ydir.name}/{month_name}")
                stats["skipped_no_year"] += 1
                continue

            dest_month = dest_trash_base / month_name
            if not DRY_RUN:
                dest_month.mkdir(parents=True, exist_ok=True)

            for root, dirs, files in os.walk(str(month_dir)):
                for fname in files:
                    src = Path(root) / fname
                    rel = src.relative_to(month_dir)
                    dst = dest_month / rel

                    if dst.exists():
                        src_h = file_hash(str(src))
                        dst_h = file_hash(str(dst))
                        if src_h and dst_h and src_h == dst_h:
                            if not DRY_RUN:
                                os.remove(str(src))
                            stats["removed_dup"] += 1
                        else:
                            if not DRY_RUN:
                                os.remove(str(src))
                            stats["removed_dup"] += 1
                            print(f"  [DEL-DUP] {src.name} (hash difiere en destino)")
                    else:
                        if not DRY_RUN:
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(src), str(dst))
                        stats["migrated"] += 1

            # Eliminar carpeta origen si queda vacía
            if not DRY_RUN:
                try:
                    month_dir.rmdir()
                except OSError:
                    pass

    # --- Migrar carpetas sin año (hebreo, temáticas) ---
    for odir in sorted(other_dirs):
        print(f"  [SKIP-CARPETA] {odir.name}/ (sin año detectable, requiere revisión manual)")
        stats["skipped_no_year"] += 1

    # --- Eliminar carpeta orphana si está vacía ---
    if not DRY_RUN:
        try:
            remaining = list(ORPHAN_TRASH.rglob("*"))
            if not remaining:
                ORPHAN_TRASH.rmdir()
                print("\n  [OK] Carpeta orphana F:\\.Papelera_Deduplicacion\\ eliminada definitivamente.")
            else:
                print(f"\n  [WARN] Carpeta orphana aún tiene contenido (carpetas sin año). No se elimina.")
        except Exception:
            pass

    return stats

# ════════════════════════════════════════════════════════════════
# FASE 1: ESCANEO Y CLASIFICACIÓN DE FOTOS SUELTAS
# ════════════════════════════════════════════════════════════════
def phase1_scan_and_classify():
    print("\n" + "=" * 60)
    print("  FASE 1: Escaneo de Fotos Sueltas en Raíces de Año")
    print("=" * 60)

    files_to_classify = []
    year_dirs = []

    for item in sorted(ROOT.iterdir()):
        if not item.is_dir():
            continue
        if is_protected(str(item)):
            continue
        name = item.name
        # Carpetas de año
        if name.isdigit() and len(name) == 4 and 2000 <= int(name) <= 2030:
            year_dirs.append(item)

    for ydir in year_dirs:
        year_num = int(ydir.name)
        for root, dirs, files in os.walk(str(ydir)):
            # Excluir subcarpetas protegidas, papeleras, y carpetas de mes ya organizadas
            root_path = Path(root)
            rel_to_year = root_path.relative_to(ydir)

            # Si estamos dentro de una carpeta de mes organizada (ej. 10-Octubre), skip
            if rel_to_year.parts and re.match(r"\d{2}-\w+", rel_to_year.parts[0]):
                continue
            # Si estamos dentro de una papelera, skip
            if any(".Papelera" in p for p in rel_to_year.parts):
                continue

            for fname in files:
                fpath = root_path / fname
                ext = fpath.suffix.lower()
                if ext not in MEDIA_EXTS:
                    continue
                # Solo archivos directamente en la raíz del año o en subcarpetas no-clasificadas
                # Excluir archivos dentro de carpetas de mes organizadas
                files_to_classify.append(fpath)

    print(f"  Archivos multimedia encontrados: {len(files_to_classify)}")
    return files_to_classify

# ════════════════════════════════════════════════════════════════
# FASE 2: DEDUPLICACIÓN + FUSIÓN EXIF
# ════════════════════════════════════════════════════════════════
def phase2_deduplicate(files):
    print("\n" + "=" * 60)
    print("  FASE 2: Deduplicación y Fusión de Metadatos")
    print("=" * 60)

    groups = defaultdict(list)
    for f in files:
        # Normalizar nombre base: quitar ext, prefijos tipo Screenshot_, etc.
        base = f.stem
        # Quitar prefijos comunes
        base = re.sub(r"^(Screenshot_|IMG-|VID-|IMG_|VID_)", "", base)
        # Extraer parte numérica del timestamp si existe
        ts_match = re.search(r"(\d{4}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2})", base)
        if ts_match:
            key = re.sub(r"[-_\s]", "", ts_match.group(1))
        else:
            key = base.lower().strip()

        groups[key].append(f)

    dups_found = 0
    groups_with_dups = 0
    for key, members in groups.items():
        if len(members) > 1:
            groups_with_dups += 1
            dups_found += len(members) - 1

    print(f"  Grupos con duplicados: {groups_with_dups}")
    print(f"  Total duplicados a procesar: {dups_found}")
    return groups

# ════════════════════════════════════════════════════════════════
# FASE 3: BASE DE DATOS
# ════════════════════════════════════════════════════════════════
def phase3_init_db():
    print("\n" + "=" * 60)
    print("  FASE 3: Inicialización de photo_catalog.db")
    print("=" * 60)

    if DRY_RUN:
        print("  [DRY RUN] Base de datos no será modificada.")
        return None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT,
            final_path TEXT,
            filename TEXT,
            file_hash TEXT,
            file_size INTEGER,
            date_taken TEXT,
            year INTEGER,
            month_folder TEXT,
            lat REAL,
            lng REAL,
            location_name TEXT,
            is_duplicate INTEGER DEFAULT 0,
            merged_from TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print(f"  [OK] Base de datos inicializada: {DB_PATH}")
    return conn

# ════════════════════════════════════════════════════════════════
# MAIN DRY RUN
# ════════════════════════════════════════════════════════════════
def main():
    mode = "[DRY RUN] (simulacion)" if DRY_RUN else "[EJECUCION REAL]"
    print(f"\n{'#' * 60}")
    print(f"  MODALIDAD: {mode}")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#' * 60}")

    # FASE 0
    trash_stats = phase0_consolidate_trash()

    # FASE 1
    files = phase1_scan_and_classify()

    # FASE 2
    dup_groups = phase2_deduplicate(files)

    # FASE 3
    conn = phase3_init_db()

    # RESUMEN
    print("\n" + "=" * 60)
    print("  RESUMEN DE SIMULACIÓN" if DRY_RUN else "  RESUMEN DE EJECUCIÓN")
    print("=" * 60)
    print(f"  Papeleras: {trash_stats['migrated']} migrados, {trash_stats['removed_dup']} eliminados (dup), {trash_stats['skipped_no_year']} carpetas sin año")
    print(f"  Fotos sueltas: {len(files)} archivos multimedia detectados")
    print(f"  Grupos deduplicados: {len([g for g in dup_groups.values() if len(g) > 1])} ({sum(len(g)-1 for g in dup_groups.values() if len(g) > 1)} duplicados)")

    if DRY_RUN:
        print("\n  [!] Para ejecutar cambios reales, re-ejecuta con:  python fases_papelera.py --execute")
    else:
        print("\n  [OK] Cambios aplicados en disco.")

    if conn:
        conn.close()

if __name__ == "__main__":
    main()
