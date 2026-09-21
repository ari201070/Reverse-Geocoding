import os
import sys
import io
import hashlib
import cv2
import numpy as np
from PIL import Image

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Search directories per user instructions
SEARCH_TARGETS = [
    ('F_Drive', 'F:/'),
    ('OneDrive', r'C:\Users\flier\OneDrive'),
    ('Dropbox', r'C:\Users\flier\Dropbox'),
    ('Pictures', r'C:\Users\flier\Pictures'),
    ('Downloads', r'C:\Users\flier\Downloads'),
    ('G_Drive', 'G:/')
]

IGNORE_DIRS = {
    'node_modules', '.git', 'AppData', '$RECYCLE.BIN', 'System Volume Information',
    'Program Files', 'Program Files (x86)', 'Windows', 'Local Settings', 'Temp',
    'Recuperado_Picasa'  # 40k raw cache dump; skip to maintain performance
}

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.webp')

# Keywords indicating schedules, timetables, duties, and greeting flyers
SCHEDULE_KEYWORDS = [
    'screenshot', 'screen', 'capture', 'excel', 'sheet', 'table',
    'schedule', 'timetable', 'duty', 'roster',
    'לוח', 'תורנות', 'תורן', 'טבלה', 'סדר', 'מערכת', 'שבוע', 'לוז', 'לו"ז',
    'shabbat', 'shalom', 'שבת', 'שלום'
]

def quick_hash(file_path):
    """Calculates fast signature to detect duplicate copies among flagged files."""
    try:
        size = os.path.getsize(file_path)
        h = hashlib.md5()
        h.update(str(size).encode())
        with open(file_path, 'rb') as f:
            h.update(f.read(32768))
            if size > 32768:
                f.seek(-min(32768, size - 32768), 2)
                h.update(f.read(32768))
        return h.hexdigest()
    except Exception:
        return None

def is_candidate_filename(filename):
    """
    Identifies if a file is a candidate for schedule, roster, WhatsApp document, or screenshot.
    Excludes high-resolution native camera files (e.g. 20251006_133936.jpg, DSCN..., P10...).
    """
    fn_low = filename.lower()
    
    # Check keywords in filename
    for kw in SCHEDULE_KEYWORDS:
        if kw in fn_low or kw in filename:
            return True, f"Nombre clave ('{kw}')"
            
    # WhatsApp image patterns
    if '-wa' in fn_low or 'wa00' in fn_low or 'whatsapp' in fn_low or fn_low.startswith('null-'):
        return True, "WhatsApp imagen"
        
    # Screenshot patterns
    if 'screenshot' in fn_low or 'capture' in fn_low:
        return True, "Captura de pantalla"
        
    return False, ""

def evaluate_image_structure(file_path):
    """
    Evaluates visual image structure (OpenCV / PIL draft):
    - White paper background ratio (> 60% = printed roster/document/sheet)
    - Grid lines (horizontal & vertical lines = spreadsheet/table)
    - Smartphone screenshot aspect ratios (tall UI)
    """
    try:
        im = Image.open(file_path)
        w, h = im.size
        ratio = max(w, h) / min(w, h)
        
        # Fast load 256px draft
        im.draft('RGB', (256, 256))
        im_rgb = im.convert('RGB')
        arr = np.array(im_rgb)
        
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        gh, gw = gray.shape
        
        # 1. High white background (printed schedule, paper document)
        white_pct = np.mean(gray > 215)
        if white_pct > 0.60:
            return True, f"Planilla / Documento impreso fondo blanco ({white_pct*100:.1f}%)"
            
        # 2. Grid lines (Excel spreadsheet / Table cells)
        edges = cv2.Canny(gray, 50, 150)
        
        k_h = cv2.getStructuringElement(cv2.MORPH_RECT, (max(1, gw // 20), 1))
        m_h = cv2.morphologyEx(edges, cv2.MORPH_OPEN, k_h)
        h_score = np.mean(m_h > 0) * 1000
        
        k_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(1, gh // 20)))
        m_v = cv2.morphologyEx(edges, cv2.MORPH_OPEN, k_v)
        v_score = np.mean(m_v > 0) * 1000
        
        grid = cv2.bitwise_and(m_h, m_v)
        grid_pts = np.sum(grid > 0)
        
        if (h_score > 6.0 and v_score > 1.0) or (v_score > 6.0 and h_score > 1.0) or grid_pts > 15:
            return True, f"Estructura de cuadrícula / Tabla Excel (Líneas H:{h_score:.1f}, V:{v_score:.1f}, Nodos:{grid_pts})"
            
        # 3. Smartphone screenshot / graphic display (tall aspect ratio > 2.05)
        if ratio > 2.05:
            edge_density = np.mean(edges > 0)
            if edge_density < 0.05:
                return True, f"Captura de pantalla de smartphone (Ratio {ratio:.2f})"
                
        return False, ""
    except Exception:
        return False, ""

def main():
    print("=" * 85)
    print("  AUDITORÍA VISUAL COMPLETA: PLANILLAS DE TURNOS, TABLAS, CRONOGRAMAS Y FLYERS")
    print("  (FASE ESTRICTA DE SOLO LECTURA Y REPORTE — PROHIBIDO BORRAR)")
    print("=" * 85)
    
    candidates = []
    
    # Phase 1: Fast directory gathering of candidate files
    for label, root_dir in SEARCH_TARGETS:
        if not os.path.exists(root_dir):
            print(f"[Aviso] Directorio no montado o ausente: {label} ({root_dir})")
            continue
            
        print(f"\nLocalizando candidatos en: {label} ({root_dir}) ...")
        found_in_target = 0
        
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    is_cand, cand_reason = is_candidate_filename(f)
                    if is_cand:
                        fp = os.path.normpath(os.path.join(root, f))
                        candidates.append({
                            'path': fp,
                            'filename': f,
                            'folder': root,
                            'cand_reason': cand_reason
                        })
                        found_in_target += 1
                        
        print(f"  └─ {label}: {found_in_target} archivos candidatos encontrados.")
        
    total_candidates = len(candidates)
    print(f"\nTotal candidatos a evaluar visualmente: {total_candidates}")
    
    if total_candidates == 0:
        print("No se encontraron archivos candidatos en el sistema.")
        sys.exit(0)
        
    # Phase 2: Visual structure evaluation on candidate files
    print("\nEvaluando estructura visual de los candidatos (OpenCV & PIL)...")
    flagged_files = []
    
    for idx, cand in enumerate(candidates):
        if idx > 0 and idx % 250 == 0:
            print(f"  ... {idx}/{total_candidates} evaluados ({len(flagged_files)} tablas/flyers detectados)")
            
        fp = cand['path']
        fn = cand['filename']
        cand_reason = cand['cand_reason']
        
        # If filename already explicitly matches a schedule/table keyword, we accept it directly
        if "Nombre clave" in cand_reason or "Captura" in cand_reason:
            try:
                sz = os.path.getsize(fp)
                flagged_files.append({
                    'path': fp,
                    'filename': fn,
                    'folder': cand['folder'],
                    'size_bytes': sz,
                    'size_mb': sz / (1024 * 1024),
                    'reason': cand_reason
                })
            except: pass
            continue
            
        # Otherwise, perform visual structure analysis
        is_table, visual_reason = evaluate_image_structure(fp)
        if is_table:
            try:
                sz = os.path.getsize(fp)
                flagged_files.append({
                    'path': fp,
                    'filename': fn,
                    'folder': cand['folder'],
                    'size_bytes': sz,
                    'size_mb': sz / (1024 * 1024),
                    'reason': visual_reason
                })
            except: pass
            
    print("\n" + "=" * 85)
    print("  REPORTE INTEGRAL DE AUDITORÍA (SOLO LECTURA)")
    print("=" * 85)
    
    total_count = len(flagged_files)
    total_bytes = sum(item['size_bytes'] for item in flagged_files)
    total_mb = total_bytes / (1024 * 1024)
    total_gb = total_bytes / (1024 * 1024 * 1024)
    
    # Group by directory
    by_folder = {}
    for item in flagged_files:
        fld = item['folder']
        by_folder.setdefault(fld, []).append(item)
        
    # Check for duplicates among the flagged files
    hash_map = {}
    for item in flagged_files:
        h = quick_hash(item['path'])
        if h:
            hash_map.setdefault(h, []).append(item)
            
    duplicate_groups = {h: items for h, items in hash_map.items() if len(items) > 1}
    dup_files_count = sum(len(items) - 1 for items in duplicate_groups.values())
    dup_bytes = sum(sum(it['size_bytes'] for it in items[1:]) for items in duplicate_groups.values())
    dup_mb = dup_bytes / (1024 * 1024)
    
    print(f"\n1. RESUMEN GENERAL:")
    print(f"  • Total de archivos de turnos / tablas / flyers encontrados:          {total_count}")
    print(f"  • Archivos que son copias duplicadas idénticas entre sí:              {dup_files_count}")
    print(f"  • Espacio total estimado a liberar si se purgan todos:               {total_mb:.2f} MB ({total_gb:.2f} GB)")
    print(f"  • Espacio que se liberaría solo purgando los duplicados repetidos:  {dup_mb:.2f} MB")
    
    print(f"\n2. DISTRIBUCIÓN POR CARPETAS PRINCIPALES (TOP 25 DONDE ESTÁN ACUMULADOS):")
    sorted_folders = sorted(by_folder.items(), key=lambda x: sum(i['size_bytes'] for i in x[1]), reverse=True)
    
    for fld, items in sorted_folders[:25]:
        fld_size_mb = sum(i['size_bytes'] for i in items) / (1024 * 1024)
        print(f"\n📁 Carpeta: {fld}")
        print(f"   Total: {len(items)} archivos | {fld_size_mb:.2f} MB")
        for it in items[:4]:
            print(f"     • {it['filename']} ({it['size_mb']:.2f} MB) -> {it['reason']}")
        if len(items) > 4:
            print(f"     ... y {len(items) - 4} archivos más en esta carpeta.")
            
    print("\n" + "=" * 85)
    print("  PAUSA DE CONTROL DE SEGURIDAD:")
    print("  [ESTADO: 100% SEGURO - NINGÚN ARCHIVO FUE MODIFICADO NI ELIMINADO]")
    print("  El escaneo ha concluido en modo de solo lectura.")
    print("  Esperando confirmación explícita del usuario antes de proceder a cualquier eliminación.")
    print("=" * 85)

if __name__ == '__main__':
    main()
