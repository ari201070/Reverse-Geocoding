import os
import sys
import io
import sqlite3
import piexif
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
F_DRIVE_ROOT = r"F:\\"

# Coordinates for Jerusalem Biblical Zoo
BIBLICAL_ZOO_LAT = 31.7454
BIBLICAL_ZOO_LNG = 35.1764
BIBLICAL_ZOO_NAME = "גן החיות התנכי"

def decode_xp_keywords(val):
    if not val:
        return ""
    if isinstance(val, (bytes, bytearray)):
        return val.decode('utf-16', errors='ignore').strip()
    elif isinstance(val, tuple):
        try:
            return bytes(val).decode('utf-16', errors='ignore').strip()
        except:
            return ""
    return ""

def main():
    print("=" * 80)
    print(f"  INICIANDO GEOLOCALIZACIÓN Y PROPAGACIÓN DE: {BIBLICAL_ZOO_NAME}")
    print("=" * 80)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # Search specifically under F:\2009\ (where the Biblical Zoo photos are located) to be ultra-fast!
        search_path = os.path.normpath("F:/2009")
        print(f"Buscando fotos físicas con el tag en {search_path}...")
        
        zoo_photos = []
        if os.path.exists(search_path):
            for root, dirs, files in os.walk(search_path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ('.jpg', '.jpeg'):
                        fp = os.path.join(root, f)
                        try:
                            exif_dict = piexif.load(fp)
                            keywords_tag = exif_dict.get('0th', {}).get(40094) # XPKeywords
                            if keywords_tag:
                                keywords_str = decode_xp_keywords(keywords_tag)
                                if BIBLICAL_ZOO_NAME in keywords_str:
                                    file_size = os.path.getsize(fp)
                                    zoo_photos.append({
                                        'path': fp, 'filename': f, 'size': file_size, 'keywords': keywords_str
                                    })
                        except: pass
                        
        print(f"Total fotos físicas encontradas con la etiqueta: {len(zoo_photos)}")
        
        if not zoo_photos:
            print("No se encontraron fotos físicas en F:/2009 con esa etiqueta.")
            sys.exit(0)
            
        updated_count = 0
        conn.execute("BEGIN TRANSACTION;")
        
        for item in zoo_photos:
            # Query DB to find matching record
            cursor = conn.execute(
                "SELECT id, file_path, lat, lng FROM photos WHERE filename = ? AND file_size = ?",
                (item['filename'], item['size'])
            )
            rows = cursor.fetchall()
            
            if rows:
                row = rows[0]
                pid = row['id']
                current_lat = row['lat']
                
                # Assign Biblical Zoo coordinates in database
                print(f"  -> ID {pid}: {item['filename']} (Actual lat: {current_lat}) -> Geolocalizando en '{BIBLICAL_ZOO_NAME}'")
                conn.execute("""
                    UPDATE photos 
                    SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                        location_name = ?, location_source = 'VISION_LANDMARK',
                        confidence_score = 0.95
                    WHERE id = ?
                """, (BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_NAME, pid))
                updated_count += 1
                
        conn.commit()
        print(f"\n¡Geolocalización finalizada! {updated_count} fotos actualizadas en la base de datos.")
        
        # 2. Spatiotemporal Neighborhood Propagation (Reverse-Geocoding)
        if updated_count > 0:
            print("\n--- EJECUTANDO VÍNCULO ESPACIO-TEMPORAL (HERENCIA DE VECINDAD) ---")
            print("Buscando fotos vecinas tomadas dentro de un rango de +/- 45 minutos en el mismo día...")
            
            # Fetch the geolocalized photos from the database
            cursor = conn.execute("""
                SELECT id, date_taken, file_path 
                FROM photos 
                WHERE location_name = ? AND location_source = 'VISION_LANDMARK'
            """, (BIBLICAL_ZOO_NAME,))
            zoo_rows = cursor.fetchall()
            
            propagated_count = 0
            conn.execute("BEGIN TRANSACTION;")
            
            for zr in zoo_rows:
                z_dt_str = zr['date_taken']
                if not z_dt_str: continue
                try:
                    # Parse datetime
                    z_dt = datetime.strptime(z_dt_str, "%Y-%m-%d %H:%M:%S")
                    date_prefix = z_dt_str[:10] # YYYY-MM-DD
                    
                    # Query other photos in 2009 without GPS taken on the same day
                    cursor2 = conn.execute("""
                        SELECT id, date_taken, file_path 
                        FROM photos 
                        WHERE (lat IS NULL OR lat = 0.0) 
                          AND date_taken IS NOT NULL 
                          AND date_taken LIKE ?
                    """, (date_prefix + "%",))
                    
                    candidates = cursor2.fetchall()
                    for cand in candidates:
                        c_dt_str = cand['date_taken']
                        try:
                            c_dt = datetime.strptime(c_dt_str, "%Y-%m-%d %H:%M:%S")
                            diff = abs((c_dt - z_dt).total_seconds()) / 60.0 # difference in minutes
                            if diff <= 45.0: # within 45 minutes!
                                print(f"    * Heredar a: {os.path.basename(cand['file_path'])} (Ruta: {cand['file_path']} | diff: {diff:.1f} min)")
                                conn.execute("""
                                    UPDATE photos 
                                    SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                                        location_name = ?, location_source = 'PUZZLE_INTERPOLATION',
                                        confidence_score = 0.90
                                WHERE id = ?
                                """, (BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_NAME, cand['id']))
                                propagated_count += 1
                        except Exception as e:
                            pass
                except Exception as e:
                    pass
                    
            conn.commit()
            print(f"\n¡Propagación completada! {propagated_count} fotos vecinas heredaron con éxito las coordenadas.")
            
    except Exception as e:
        conn.rollback()
        print(f"Error crítico en el proceso: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
