import os
import sys
import io
import sqlite3
import glob
import piexif

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
F_DRIVE_ROOT = r"F:\\"

# Bounding box of Rome
ROME_MIN_LAT = 41.8
ROME_MAX_LAT = 42.0
ROME_MIN_LNG = 12.4
ROME_MAX_LNG = 12.6

# Coordinates for Jerusalem Biblical Zoo
BIBLICAL_ZOO_LAT = 31.7454
BIBLICAL_ZOO_LNG = 35.1764
BIBLICAL_ZOO_NAME = "גן החיות התנכי"

def parse_rational(rat):
    if not rat or len(rat) != 2:
        return 0.0
    return float(rat[0]) / float(rat[1]) if rat[1] != 0 else 0.0

def exif_gps_to_decimal(gps_lat, lat_ref, gps_lng, lng_ref):
    try:
        lat = parse_rational(gps_lat[0]) + parse_rational(gps_lat[1])/60.0 + parse_rational(gps_lat[2])/3600.0
        lng = parse_rational(gps_lng[0]) + parse_rational(gps_lng[1])/60.0 + parse_rational(gps_lng[2])/3600.0
        
        # Decode refs
        if isinstance(lat_ref, bytes):
            lat_ref = lat_ref.decode(errors='ignore')
        if isinstance(lng_ref, bytes):
            lng_ref = lng_ref.decode(errors='ignore')
            
        if lat_ref == 'S':
            lat = -lat
        if lng_ref == 'W':
            lng = -lng
        return lat, lng
    except Exception:
        return None, None

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
    apply_changes = "--apply" in sys.argv
    mode = "[EJECUCIÓN REAL]" if apply_changes else "[MODO SIMULACIÓN - DRY RUN]"
    
    print("=" * 85)
    print(f"  {mode} REPARACIÓN FÍSICA DE EXIF (ROMA) & GEOLOCALIZACIÓN POR TAG")
    print("=" * 85)
    
    # 1. Physical Saneamiento of Rome/Portuno corruptions
    print("\n--- PASO 1: Saneamiento de Cabeceras EXIF Corruptas en Disco F: ---")
    print("Escaneando carpetas físicas del disco F: (excluyendo el año de Italia: 2023)...")
    
    healed_files_count = 0
    scanned_files_count = 0
    
    # Loop through year folders in F: except 2023
    for year_folder in sorted(os.listdir(F_DRIVE_ROOT)):
        year_path = os.path.join(F_DRIVE_ROOT, year_folder)
        if not os.path.isdir(year_path) or year_folder == '2023' or not year_folder.isdigit():
            continue
            
        # Walk through month folders in this year
        for root, dirs, files in os.walk(year_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ('.jpg', '.jpeg'):
                    fp = os.path.join(root, f)
                    scanned_files_count += 1
                    
                    try:
                        exif_dict = piexif.load(fp)
                        zeroth = exif_dict.get('0th', {})
                        gps = exif_dict.get('GPS', {})
                        
                        is_corrupted = False
                        reason = ""
                        
                        # Check Rome coordinates
                        if gps:
                            lat_val = gps.get(piexif.GPSIFD.GPSLatitude)
                            lat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
                            lng_val = gps.get(piexif.GPSIFD.GPSLongitude)
                            lng_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)
                            
                            if lat_val and lat_ref and lng_val and lng_ref:
                                d_lat, d_lng = exif_gps_to_decimal(lat_val, lat_ref, lng_val, lng_ref)
                                if d_lat and d_lng:
                                    if ROME_MIN_LAT <= d_lat <= ROME_MAX_LAT and ROME_MIN_LNG <= d_lng <= ROME_MAX_LNG:
                                        is_corrupted = True
                                        reason = f"Coordenadas de Roma detectadas: ({d_lat:.4f}, {d_lng:.4f})"
                                        
                        # Check Windows Keywords
                        keywords_tag = zeroth.get(40094) # 0x9c9e XPKeywords
                        if keywords_tag:
                            keywords_str = decode_xp_keywords(keywords_tag)
                            if 'Portuno' in keywords_str or 'Roma' in keywords_str or 'Italia' in keywords_str:
                                is_corrupted = True
                                reason = f"Keywords de Roma detectadas: '{keywords_str}'"
                                
                        if is_corrupted:
                            print(f"\n[CORRUPCIÓN] {os.path.relpath(fp, F_DRIVE_ROOT)}")
                            print(f"             Causa: {reason}")
                            
                            if apply_changes:
                                # Remove GPS IFD
                                exif_dict.pop('GPS', None)
                                # Remove Windows XP properties
                                zeroth.pop(40094, None) # XPKeywords
                                zeroth.pop(40093, None) # XPSubject
                                zeroth.pop(40095, None) # XPComment
                                
                                # Insert cleaned EXIF back
                                exif_bytes = piexif.dump(exif_dict)
                                piexif.insert(exif_bytes, fp)
                                print(f"             -> [SANEADO] EXIF limpiado físicamente con éxito.")
                                
                            healed_files_count += 1
                            
                    except Exception as e:
                        pass
                        
    print(f"\nSaneamiento finalizado. Escaneados: {scanned_files_count} JPEGs. Corruptos: {healed_files_count}")
    
    # 2. Inyección de Coordenadas por Tag ("גן החיות התנכי")
    print("\n--- PASO 2: Geolocalización por Tag en Base de Datos ---")
    print(f"Buscando fotos con tag '{BIBLICAL_ZOO_NAME}'...")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # We will scan all files on disk under F: to check if they have "גן החיות התנכי" inside their EXIF XPKeywords (tag 40094)
        print("Escaneando disco físico en busca de la etiqueta...")
        zoo_photos_found = []
        
        for root, dirs, files in os.walk(F_DRIVE_ROOT):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ('.jpg', '.jpeg'):
                    fp = os.path.join(root, f)
                    try:
                        exif_dict = piexif.load(fp)
                        keywords_tag = exif_dict.get('0th', {}).get(40094)
                        if keywords_tag:
                            keywords_str = decode_xp_keywords(keywords_tag)
                            if BIBLICAL_ZOO_NAME in keywords_str:
                                # Found! Let's check size to match with database
                                file_size = os.path.getsize(fp)
                                zoo_photos_found.append({
                                    'path': fp, 'filename': f, 'size': file_size, 'keywords': keywords_str
                                })
                    except: pass
                    
        print(f"Total fotos físicas encontradas con el tag '{BIBLICAL_ZOO_NAME}': {len(zoo_photos_found)}")
        
        if zoo_photos_found:
            updated_zoo_count = 0
            for item in zoo_photos_found:
                # Find DB record
                cursor = conn.execute(
                    "SELECT id, file_path, lat, lng, location_name FROM photos WHERE filename = ? AND file_size = ?", 
                    (item['filename'], item['size'])
                )
                rows = cursor.fetchall()
                if rows:
                    row = rows[0]
                    pid = row['id']
                    current_lat = row['lat']
                    
                    if current_lat is None or current_lat == 0.0:
                        print(f"\n[GEO-TAG] ID {pid}: {item['filename']} -> Asignando ubicación '{BIBLICAL_ZOO_NAME}'")
                        print(f"          Ruta: {item['path']}")
                        
                        if apply_changes:
                            conn.execute("""
                                UPDATE photos 
                                SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                                    location_name = ?, location_source = 'VISION_LANDMARK',
                                    confidence_score = 0.95
                                WHERE id = ?
                            """, (BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_NAME, pid))
                            conn.commit()
                            print("          -> [DB] Coordenadas inyectadas en base de datos.")
                        updated_zoo_count += 1
                        
            print(f"\nFotos de 'גן החיות התנכי' geolocalizadas con éxito: {updated_zoo_count}")
            
            # Now let's trigger spatiotemporal propagation for these newly geolocalized photos!
            # E.g. other photos taken on the same day and month nearby!
            # Since we have the DB open, we can run a simple cluster-time inheritance.
            if apply_changes and updated_zoo_count > 0:
                print("\n--- PASO 3: Propagación Espacio-Temporal de Vecindad (Reverse-Geocoding) ---")
                # For each newly geolocalized photo, find photos taken within +/- 45 minutes on the same day
                # and inherit coordinates!
                print("Ejecutando propagación espacio-temporal en vecindad de 45 minutos...")
                
                # Fetch our newly geolocalized zoo photos
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
                        
                        # Query other photos without GPS taken on the same day
                        cursor2 = conn.execute("""
                            SELECT id, date_taken, file_path 
                            FROM photos 
                            WHERE (lat IS NULL OR lat = 0.0) 
                              AND date_taken IS NOT NULL 
                              AND date_taken LIKE ?
                        """, (z_dt_str[:10] + "%",))
                        
                        candidates = cursor2.fetchall()
                        for cand in candidates:
                            c_dt_str = cand['date_taken']
                            try:
                                c_dt = datetime.strptime(c_dt_str, "%Y-%m-%d %H:%M:%S")
                                diff = abs((c_dt - z_dt).total_seconds()) / 60.0 # difference in minutes
                                if diff <= 45.0: # within 45 minutes!
                                    print(f"  -> Propagar: {os.path.basename(cand['file_path'])} (diff: {diff:.1f} min)")
                                    conn.execute("""
                                        UPDATE photos 
                                        SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                                            location_name = ?, location_source = 'PUZZLE_INTERPOLATION',
                                            confidence_score = 0.90
                                        WHERE id = ?
                                    """, (BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_LAT, BIBLICAL_ZOO_LNG, BIBLICAL_ZOO_NAME, cand['id']))
                                    propagated_count += 1
                            except: pass
                    except: pass
                    
                conn.commit()
                print(f"\n¡Propagación completada! {propagated_count} fotos vecinas heredaron coordenadas.")
                
        else:
            print("No se encontraron fotos físicas con el tag 'גן החיות התנכי' en el disco F:.")
            
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un fallo en el proceso: {e}")
        sys.exit(1)
    finally:
        conn.close()
        
    if not apply_changes:
        print("\n" + "="*50)
        print("  AVISO: Modo simulación activo. No se hicieron cambios permanentes.")
        print("  Para aplicar las reparaciones físicas y geolocalizar por tag, ejecuta:")
        print("    python apps/backend/scripts/clean_physical_exif_corruption.py --apply")
        print("="*50)

if __name__ == '__main__':
    main()
