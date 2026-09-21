import os
import sys
import io
import subprocess
import sqlite3
import tempfile

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

TARGET_FOLDERS = [
    r"F:\2025\10-Octubre",
    r"F:\2025\09-Septiembre",
    r"F:\2025\12-Diciembre",
    r"F:\2026\01-Enero",
    r"F:\2025\11-Noviembre"
]

def main():
    print("=" * 85)
    print("  MIGRACIÓN EN BATCH ULTRA-RÁPIDA DE METADATOS HEIC -> JPG (EXIFTOOL BATCH)")
    print("=" * 85)
    
    twins = []
    
    for fld in TARGET_FOLDERS:
        if not os.path.exists(fld):
            continue
        files = os.listdir(fld)
        file_map = {f.lower(): f for f in files}
        
        for f in files:
            if f.lower().endswith('.heic'):
                base, _ = os.path.splitext(f)
                jpg_name = base + ".jpg"
                jpeg_name = base + ".jpeg"
                
                matched_jpg = None
                if jpg_name.lower() in file_map:
                    matched_jpg = file_map[jpg_name.lower()]
                elif jpeg_name.lower() in file_map:
                    matched_jpg = file_map[jpeg_name.lower()]
                    
                if matched_jpg:
                    heic_path = os.path.join(fld, f)
                    jpg_path = os.path.join(fld, matched_jpg)
                    twins.append((heic_path, jpg_path))
                    
    print(f"Total pares de gemelas restantes por migrar: {len(twins)}")
    
    if not twins:
        print("No hay gemelas pendientes.")
    else:
        # Create an exiftool argfile to process all remaining twins in one single batch!
        argfile_path = os.path.join(tempfile.gettempdir(), "exiftool_args.txt")
        with open(argfile_path, "w", encoding="utf-8") as f:
            for idx, (heic_path, jpg_path) in enumerate(twins):
                f.write("-overwrite_original\n")
                f.write("-tagsFromFile\n")
                f.write(f"{heic_path}\n")
                f.write("-all:all\n")
                f.write(f"{jpg_path}\n")
                if idx < len(twins) - 1:
                    f.write("-execute\n")
                    
        print(f"Ejecutando ExifTool en lote para {len(twins)} fotos...")
        res = subprocess.run(['exiftool', '-@', argfile_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("ExifTool finalizó. Eliminando archivos .heic procesados...")
        
        deleted_count = 0
        total_freed = 0
        for heic_path, jpg_path in twins:
            try:
                sz = os.path.getsize(heic_path)
                os.remove(heic_path)
                deleted_count += 1
                total_freed += sz
            except Exception as e:
                print(f"Error al eliminar {heic_path}: {e}")
                
        try:
            os.remove(argfile_path)
        except: pass
        
        print(f"  - Archivos .heic eliminados con éxito: {deleted_count}/{len(twins)}")
        print(f"  - Espacio liberado en este lote:       {total_freed / (1024*1024):.2f} MB")
        
    # Synchronize photo_catalog.db
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("DELETE FROM photos WHERE file_ext = '.heic' OR file_ext = '.HEIC'")
        deleted_db = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"\nSincronización DB: eliminados {deleted_db} registros de .heic en photo_catalog.db")
        
    print("=" * 85)

if __name__ == '__main__':
    main()
