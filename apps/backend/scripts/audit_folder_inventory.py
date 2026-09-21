import os
import sys
import io
import sqlite3
import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

# Exact physical folders of the key trips and regional archives
TARGET_AUDIT_FOLDERS = [
    ("Creta 2013 & Bat Mitzvah (Julio)", r"F:\2013\07-Julio"),
    ("Chipre 2023 (Agosto)", r"F:\2023\08-Agosto"),
    ("Italia 2023 (Octubre)", r"F:\2023\10-Octubre"),
    ("Bosnia 2023 (Mayo)", r"F:\2023\05-Mayo"),
    ("Israel 2009 (Zoológico Bíblico / Dic)", r"F:\2009\12-Diciembre"),
    ("Israel 2010 (Vacaciones Agosto)", r"F:\2010\08-Agosto"),
    ("Argentina 2011 (Lago Puelo & Calafate)", r"F:\2011\11-Noviembre"),
    ("Argentina 2025 (Bariloche & Traful)", r"F:\2025\10-Octubre")
]

STATUS_MAP = {
    'EXIF_GPS': 'Existente / Intacta (EXIF nativo)',
    'VISION_LANDMARK': 'Ubicación agregada vía VISION_LANDMARK',
    'PUZZLE_INTERPOLATION': 'Ubicación heredada H3 (Modo Puzzle)',
    'VERIFIED_GEOJSON_POI': 'Ubicación verificada GEOJSON_POI',
    'VOUCHER_INHERITANCE': 'Ubicación heredada VOUCHER_INHERITANCE',
    'STAGE_DAILY_AVERAGE': 'Centroide diario STAGE_DAILY_AVERAGE',
    'FILENAME_VOUCHER_MATCH': 'Ubicación asignada FILENAME_VOUCHER',
    None: 'Sin geolocalizar (SIN_GEO)'
}

def format_size(bytes_val):
    if bytes_val is None:
        return "0 KB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    return f"{bytes_val / 1024:.1f} KB"

def extract_file_creation_date(st):
    try:
        ts = st.st_ctime if hasattr(st, 'st_ctime') else st.st_mtime
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Desconocida"

def extract_correlative_number(filename):
    import re
    numbers = [int(n) for n in re.findall(r'\d+', filename)]
    return tuple(numbers) if numbers else (999999, filename)

def main():
    print("=" * 115)
    print("  AUDITORÍA Y TABLA COMPARATIVA DE FOTOS (NUEVAS Y EXISTENTES)")
    print("  [MODO EXCLUSIVO DE LECTURA Y REPORTE — CERO MODIFICACIONES EN DISCO]")
    print("=" * 115)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Base de datos no encontrada en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Pre-load metadata from database for instant lookup
    cursor = conn.execute("SELECT filename, file_size, date_taken, location_source, lat, lng, location_name FROM photos")
    db_index = {}
    for r in cursor.fetchall():
        db_index[r['filename'].lower()] = r
        
    total_audited_all = 0
    stats_all_sources = {}
    
    for label, folder_path in TARGET_AUDIT_FOLDERS:
        if not os.path.exists(folder_path):
            continue
            
        disk_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.mov', '.mp4'))]
        if not disk_files:
            continue
            
        print(f"\n📁 CARPETA: {label}")
        print(f"   Ruta física: {folder_path} ({len(disk_files)} archivos en disco)")
        print("-" * 115)
        
        disk_files.sort(key=extract_correlative_number)
        table_rows = []
        
        for idx, fn in enumerate(disk_files, start=1):
            fp = os.path.join(folder_path, fn)
            try:
                st = os.stat(fp)
                file_size = st.st_size
                creation_date_str = extract_file_creation_date(st)
            except:
                file_size = 0
                creation_date_str = "Desconocida"
                
            db_row = db_index.get(fn.lower())
            
            date_taken_str = "Sin EXIF"
            loc_src = None
            if db_row:
                date_taken_str = db_row['date_taken'] or "Sin EXIF"
                loc_src = db_row['location_source']
                
            status_desc = STATUS_MAP.get(loc_src, 'Sin geolocalizar (SIN_GEO)')
            stats_all_sources[status_desc] = stats_all_sources.get(status_desc, 0) + 1
            
            table_rows.append({
                'index': idx,
                'filename': fn,
                'date_taken': date_taken_str,
                'creation_date': creation_date_str,
                'status': status_desc,
                'size': format_size(file_size)
            })
            
        total_audited_all += len(table_rows)
        
        # Print table header
        print(f"| {'#':<4} | {'Archivo':<36} | {'Fecha Toma (EXIF)':<20} | {'Fecha Creación':<19} | {'Estado / Modificación':<38} | {'Tamaño':<9} |")
        print(f"|{'-'*6}|{'-'*38}|{'-'*22}|{'-'*21}|{'-'*40}|{'-'*11}|")
        
        # Display rows
        if len(table_rows) <= 20:
            display_rows = table_rows
        else:
            display_rows = table_rows[:15]
            
        for r in display_rows:
            fn_disp = r['filename'][:34] + ".." if len(r['filename']) > 36 else r['filename']
            st_disp = r['status'][:36] + ".." if len(r['status']) > 38 else r['status']
            print(f"| {r['index']:<4} | {fn_disp:<36} | {r['date_taken']:<20} | {r['creation_date']:<19} | {st_disp:<38} | {r['size']:<9} |")
            
        if len(table_rows) > 20:
            print(f"| ...  | ... ({len(table_rows) - 20} archivos correlativos adicionales) ...")
            for r in table_rows[-5:]:
                fn_disp = r['filename'][:34] + ".." if len(r['filename']) > 36 else r['filename']
                st_disp = r['status'][:36] + ".." if len(r['status']) > 38 else r['status']
                print(f"| {r['index']:<4} | {fn_disp:<36} | {r['date_taken']:<20} | {r['creation_date']:<19} | {st_disp:<38} | {r['size']:<9} |")
                
        print("-" * 115)
        print(f"Total en esta carpeta: {len(table_rows)} archivos inspeccionados.")
        
    conn.close()
    
    # Final Consolidated Report
    print("\n" + "=" * 115)
    print("  REPORTE CONSOLIDADO GLOBAL DE LA AUDITORÍA")
    print("=" * 115)
    print(f"Total global de archivos inspeccionados en las carpetas de enriquecimiento: {total_audited_all}")
    print("\nDesglose por Estado / Modificación:")
    for status, count in sorted(stats_all_sources.items(), key=lambda x: -x[1]):
        pct = (count / total_audited_all) * 100 if total_audited_all else 0
        print(f"  • {status:<42}: {count:>5} archivos ({pct:5.2f}%)")
    print("=" * 115)

if __name__ == '__main__':
    main()
