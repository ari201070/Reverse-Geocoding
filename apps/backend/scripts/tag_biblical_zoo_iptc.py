import os
import sys
import io
import sqlite3
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
F_DRIVE_ROOT = r"F:\\"

# Target tag: "גן החיות התנכי" (Jerusalem Biblical Zoo)
TARGET_TAG_NAME = "גן החיות התנכי"
BIBLICAL_ZOO_LAT = 31.7454
BIBLICAL_ZOO_LNG = 35.1764

# Byte sequences of "גן החיות התנכי" in different encodings (CP1255, UTF-8, UTF-16LE)
TARGET_BYTE_SEQUENCES = [
    b'\xe2\xef \xe4\xe7\xe9\xe5\xfa \xe4\xfa\xf0\xeb\xe9',  # Windows-1255 (IPTC)
    "גן החיות התנכי".encode('utf-8'),                     # UTF-8 (XMP)
    "גן החיות התנכי".encode('utf-16le'),                 # UTF-16LE (XPKeywords)
]

def contains_target_tag(file_path):
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            
        for seq in TARGET_BYTE_SEQUENCES:
            if seq in content:
                return True
    except Exception:
        pass
    return False

def main():
    apply_changes = "--apply" in sys.argv
    mode = "[EJECUCIÓN REAL]" if apply_changes else "[MODO SIMULACIÓN - DRY RUN]"
    
    print("=" * 80)
    print(f"  {mode} GEOLOCALIZACIÓN EXTRAPOLADA POR TAG IPTC / BINARIO")
    print(f"  Tag objetivo: '{TARGET_TAG_NAME}'")
    print(f"  Coordenadas:  ({BIBLICAL_ZOO_LAT}, {BIBLICAL_ZOO_LNG})")
    print("=" * 80)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # We will scan F:\2009 (which is where the 2009 zoo trip files are)
        search_path = os.path.normpath("F:/2009")
        print(f"\nEscaneando de forma rápida {search_path} en busca de la firma binaria de '{TARGET_TAG_NAME}'...")
        
        found_files = []
        if os.path.exists(search_path):
            for root, dirs, files in os.walk(search_path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ('.jpg', '.jpeg'):
                        fp = os.path.join(root, f)
                        if contains_target_tag(fp):
                            file_size = os.path.getsize(fp)
                            found_files.append({
                                'path': fp, 'filename': f, 'size': file_size
                            })
                            
        print(f"Total fotos físicas encontradas con la etiqueta '{TARGET_TAG_NAME}' en el disco: {len(found_files)}")
        
        if not found_files:
            print("No se encontraron fotos con la firma binaria del tag.")
            sys.exit(0)
            
        updated_count = 0
        conn.execute("BEGIN TRANSACTION;")
        
        for item in found_files:
            # Query DB to find matching record
            cursor = conn.execute(
                "SELECT id, file_path, lat, lng, date_taken FROM photos WHERE filename = ? AND file_size = ?",
                (item['filename'], item['size'])
            )
            rows = cursor.fetchall()
            
            if rows:
                row = rows[0]
                pid = row['id']
                current_lat = row['lat']
                
                # Check if it lacks coordinates or has incorrect coordinates
                if current_lat is None or current_lat == 0.0 or current_lat == 41.8933: # Clean if null or corrupt Rome
                    print(f"  -> ID {pid}: {item['filename']} -> Asignando ubicación '{TARGET_TAG_NAME}'")
                    print(f"             Ruta: {item['path']}")
                    
                    if apply_changes:
                        conn.execute("""
                            UPDATE photos 
                            SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                                location_name = ?, location_source = 'VISION_LANDMARK',
                                confidence_score = 0.95
                            WHERE id = ?
                        """, (BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, TARGET_TAG_NAME, pid))
                    updated_count += 1
                    
        conn.commit()
        print(f"\n¡Geolocalización por tag completada! Fotos actualizadas en base de datos: {updated_count}")
        
        # 2. Spatiotemporal Neighborhood Propagation (Reverse-Geocoding)
        if updated_count > 0:
            print("\n--- PASO 2: PROPAGACIÓN ESPACIO-TEMPORAL DE VECINDAD (REVERSE-GEOCODING) ---")
            print("Buscando fotos vecinas tomadas dentro de un rango de +/- 45 minutos en el mismo día para heredar...")
            
            # Fetch the geolocalized photos from the database
            cursor = conn.execute("""
                SELECT id, date_taken, file_path 
                FROM photos 
                WHERE location_name = ? AND location_source = 'VISION_LANDMARK'
            """, (TARGET_TAG_NAME,))
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
                                print(f"    * Herencia para: {os.path.basename(cand['file_path'])} (diff: {diff:.1f} min)")
                                if apply_changes:
                                    conn.execute("""
                                        UPDATE photos 
                                        SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                                            location_name = ?, location_source = 'PUZZLE_INTERPOLATION',
                                            confidence_score = 0.90
                                        WHERE id = ?
                                    """, (BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, TARGET_TAG_NAME, cand['id']))
                                propagated_count += 1
                        except: pass
                except: pass
                
            conn.commit()
            print(f"\n¡Propagación completada! Fotos vecinas que heredaron coordenadas: {propagated_count}")
            
    except Exception as e:
        conn.rollback()
        print(f"Error crítico en el proceso: {e}")
        sys.exit(1)
    finally:
        conn.close()
        
    if not apply_changes:
        print("\n" + "="*50)
        print("  AVISO: Modo simulación activo. No se hicieron cambios permanentes.")
        print("  Para aplicar las reparaciones y la geolocalización por tag, ejecuta:")
        print("    python apps/backend/scripts/tag_biblical_zoo_iptc.py --apply")
        print("="*50)

if __name__ == '__main__':
    main()
