import os
import sys
import shutil
import sqlite3

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

AGOS_DIR = r"F:\2026\08-Agosto"
OCT_DIR = r"F:\2025\10-Octubre"
DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

def main():
    print("=" * 80)
    print("  LIMPIEZA DEFINITIVA DE F:\\2026\\08-Agosto")
    print("=" * 80)
    
    if not os.path.exists(AGOS_DIR):
        print(f"Aviso: La carpeta {AGOS_DIR} no existe.")
        sys.exit(0)
        
    files = os.listdir(AGOS_DIR)
    print(f"Archivos encontrados en {AGOS_DIR}: {len(files)}")
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Handle the 3 real trip photos
    for fn in ['Antiguo puente de Cruce de los Andes.jpg', 'Villa_Traful.jpg']:
        src = os.path.join(AGOS_DIR, fn)
        dst = os.path.join(OCT_DIR, fn)
        if os.path.exists(src):
            if not os.path.exists(dst):
                shutil.move(src, dst)
                print(f"  [MOVIDO] {fn} -> {OCT_DIR}")
                # Update DB
                conn.execute("""
                    UPDATE photos 
                    SET file_path = ?, trip_name = 'argentina-2025', country = 'Argentina' 
                    WHERE filename = ?
                """, (dst, fn))
            else:
                os.remove(src)
                print(f"  [YA EXISTÍA EN DESTINO] Eliminado clon de {fn}")
                
    # Taxi Ezeiza is already in 2025/09-Septiembre
    taxi_src = os.path.join(AGOS_DIR, 'Taxi-Ezeiza_Dia.0.jpg')
    if os.path.exists(taxi_src):
        os.remove(taxi_src)
        print("  [DUPLICADO PURGADO] Taxi-Ezeiza_Dia.0.jpg (ya existe en F:\\2025\\09-Septiembre)")
        
    conn.commit()
    conn.close()
    
    # 2. Delete the 679 thumb_*.jpg files
    deleted_thumbs = 0
    remaining_files = os.listdir(AGOS_DIR)
    for f in remaining_files:
        fp = os.path.join(AGOS_DIR, f)
        if f.startswith('thumb_'):
            try:
                os.remove(fp)
                deleted_thumbs += 1
            except Exception as e:
                print(f"Error borrando {f}: {e}")
                
    print(f"  [MINIATURAS PURGADAS] {deleted_thumbs} archivos thumb_*.jpg eliminados.")
    
    # 3. Remove directory
    try:
        if not os.listdir(AGOS_DIR):
            os.rmdir(AGOS_DIR)
            print(f"\n¡ÉXITO! Carpeta {AGOS_DIR} eliminada por completo.")
        else:
            print(f"Aviso: Quedaron archivos en {AGOS_DIR}: {os.listdir(AGOS_DIR)}")
    except Exception as e:
        print(f"Error al eliminar carpeta {AGOS_DIR}: {e}")
        
    print("=" * 80)

if __name__ == '__main__':
    main()
