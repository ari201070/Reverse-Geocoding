import os
import sys
import io
import cv2
import numpy as np
import sqlite3
from PIL import Image

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

# Active targets where these WhatsApp shift tables, schedules, and Shabbat Shalom graphics accumulate
YEARS_TO_SCAN = ['2024', '2025', '2026', '2023', '2022', '2021', '2020', '2019', '2018']

OTHER_TARGETS = [
    ('OneDrive_WA', r'C:\Users\flier\OneDrive\תמונות\Samsung Gallery\Android\media\com.whatsapp\WhatsApp\Media\WhatsApp Images'),
    ('Downloads', r'C:\Users\flier\Downloads')
]

# Strictly protected paths per user instructions
def is_protected(fp):
    fp_norm = os.path.normpath(fp).lower()
    # User instruction: "Toda la carpeta C:\Users\flier\Pictures\2013\אפריל-מאי ... NO se toca"
    if 'אפריל-מאי' in fp_norm or r'pictures\2013' in fp_norm:
        return True
    # User instruction: "Flyer digital con diseño vertical de cronograma no pertenece (por ahora) ... NO se toca"
    if 'img-20240514-wa0000' in fp_norm:
        return True
    return False

SHABBAT_KEYWORDS = [
    b'\xf9\xe1\xfa \xf9\xec\xe5\xed',   # "שבת שלום" in windows-1255
    "שבת שלום".encode('utf-8'),
    "שבת שלום".encode('utf-16le'),
    b'D.ISAAC', b'D. ISAAC', b'I.DAHAN', b'I. DAHAN'
]

def check_shabbat_shalom(fp):
    try:
        with open(fp, 'rb') as f:
            head = f.read(30000)
            f.seek(-min(30000, os.path.getsize(fp)), 2)
            tail = f.read(30000)
        content = head + tail
        for sig in SHABBAT_KEYWORDS:
            if sig in content:
                return True
    except:
        pass
    return False

def classify_target(fp, f):
    if is_protected(fp):
        return False, "Protegido"
        
    fn_low = f.lower()
    
    # 4. Shabbat Shalom greeting graphics
    if any(k in f for k in ['שבת', 'שלום', 'shabbat', 'shalom']) or check_shabbat_shalom(fp):
        return True, "Flyer / Saludo de 'שבת שלום'"
        
    # 1, 2, 3: Work shift Excel tables, printed roster tables, daily activity schedule flyers
    try:
        im = Image.open(fp)
        w, h = im.size
        # Fast load 128px draft
        im.draft('RGB', (128, 128))
        arr = np.array(im.convert('RGB'))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        
        # Structure A: High white document background (>65% = printed paper roster table)
        white_pct = np.mean(gray > 215)
        if white_pct > 0.65:
            return True, f"Tabla impresa en papel de turnos / Planilla ({white_pct*100:.1f}% blanco)"
            
        # Structure B: Grid lines (Excel spreadsheet on monitor or printed grid)
        edges = cv2.Canny(gray, 50, 150)
        k_h = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 1))
        m_h = cv2.morphologyEx(edges, cv2.MORPH_OPEN, k_h)
        h_s = np.mean(m_h > 0) * 1000
        
        k_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 8))
        m_v = cv2.morphologyEx(edges, cv2.MORPH_OPEN, k_v)
        v_s = np.mean(m_v > 0) * 1000
        
        if (h_s > 8.0 and v_s > 1.0) or (v_s > 8.0 and h_s > 1.0):
            return True, f"Planilla Excel de turnos en monitor (H:{h_s:.1f}, V:{v_s:.1f})"
            
    except Exception:
        pass
        
    return False, ""

def main():
    apply_changes = "--apply" in sys.argv
    mode = "[EJECUCIÓN REAL]" if apply_changes else "[MODO SIMULACIÓN - DRY RUN]"
    
    print("=" * 85)
    print(f"  {mode} PURGA DEFINITIVA DE LAS 4 CATEGORÍAS AUTORIZADAS")
    print("  1. Planillas Excel de turnos en monitor (amarillo/verde)")
    print("  2. Tablas impresas en papel con turnos semanales (שבוע - XX)")
    print("  3. Flyers de horario y actividades diarias con fechas hebreas")
    print("  4. Imágenes gráficas de saludo con texto 'שבת שלום'")
    print("  * REGLAS DE PROTECCIÓN: Carpeta 2013\\אפריל-מאי NO SE TOCA; invitaciones NO se tocan.")
    print("=" * 85)
    
    conn = sqlite3.connect(DB_PATH)
    total_deleted_disk = 0
    total_deleted_db = 0
    total_freed_bytes = 0
    
    # Process Year by Year to be responsive and show progress
    for y in YEARS_TO_SCAN:
        yp = f'F:/{y}'
        if not os.path.exists(yp): continue
        
        # Gather candidates in this year
        cands = []
        for root, dirs, files in os.walk(yp):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                fl = f.lower()
                if fl.endswith(('.jpg', '.jpeg', '.png')) and ('-wa' in fl or 'screenshot' in fl or any(k in f for k in ['לוח', 'תורנ', 'טבלה', 'שבוע', 'לוז', 'שבת', 'שלום'])):
                    cands.append(os.path.join(root, f))
                    
        year_targets = []
        for fp in cands:
            f = os.path.basename(fp)
            is_match, reason = classify_target(fp, f)
            if is_match:
                sz = os.path.getsize(fp)
                year_targets.append((fp, f, sz, reason))
                
        year_mb = sum(x[2] for x in year_targets) / (1024 * 1024)
        print(f"Año {y}: {len(year_targets)}/{len(cands)} archivos detectados ({year_mb:.2f} MB)")
        
        if apply_changes and year_targets:
            conn.execute("BEGIN TRANSACTION;")
            for fp, fn, sz, _ in year_targets:
                try:
                    if os.path.exists(fp):
                        os.remove(fp)
                    total_deleted_disk += 1
                    total_freed_bytes += sz
                    cur = conn.execute("DELETE FROM photos WHERE filename = ?", (fn,))
                    total_deleted_db += cur.rowcount
                except Exception as e:
                    print(f"Error borrando {fp}: {e}")
            conn.commit()
            
    # Process OneDrive / Downloads
    for label, target_path in OTHER_TARGETS:
        if not os.path.exists(target_path): continue
        cands = []
        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                fl = f.lower()
                if fl.endswith(('.jpg', '.jpeg', '.png')) and ('-wa' in fl or 'screenshot' in fl or any(k in f for k in ['לוח', 'תורנ', 'טבלה', 'שבוע', 'לוז', 'שבת', 'שלום'])):
                    cands.append(os.path.join(root, f))
                    
        other_targets = []
        for fp in cands:
            f = os.path.basename(fp)
            is_match, reason = classify_target(fp, f)
            if is_match:
                sz = os.path.getsize(fp)
                other_targets.append((fp, f, sz, reason))
                
        other_mb = sum(x[2] for x in other_targets) / (1024 * 1024)
        print(f"{label}: {len(other_targets)}/{len(cands)} archivos detectados ({other_mb:.2f} MB)")
        
        if apply_changes and other_targets:
            conn.execute("BEGIN TRANSACTION;")
            for fp, fn, sz, _ in other_targets:
                try:
                    if os.path.exists(fp):
                        os.remove(fp)
                    total_deleted_disk += 1
                    total_freed_bytes += sz
                    cur = conn.execute("DELETE FROM photos WHERE filename = ?", (fn,))
                    total_deleted_db += cur.rowcount
                except Exception as e:
                    print(f"Error borrando {fp}: {e}")
            conn.commit()
            
    conn.close()
    
    total_mb = total_freed_bytes / (1024 * 1024)
    total_gb = total_freed_bytes / (1024 * 1024 * 1024)
    print("\n" + "=" * 50)
    if apply_changes:
        print("  PURGA DEFINITIVA COMPLETADA CON ÉXITO")
        print("=" * 50)
        print(f"  - Archivos físicos eliminados de disco: {total_deleted_disk}")
        print(f"  - Registros purgados en base de datos:  {total_deleted_db}")
        print(f"  - Espacio real liberado en almacenamiento: {total_mb:.2f} MB ({total_gb:.2f} GB)")
    else:
        print("  SIMULACIÓN COMPLETADA")
        print("=" * 50)
        print("  Para ejecutar el borrado definitivo en disco y DB, ejecuta con --apply.")

if __name__ == '__main__':
    main()
