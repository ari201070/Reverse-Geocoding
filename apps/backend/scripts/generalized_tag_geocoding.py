import os
import sys
import io
import sqlite3
import json
from datetime import datetime

try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
BOOKINGS_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\apps\backend\src\data\initialBookings.json"

# Dictionary of specialized Hebrew/English landmark coordinates from our historical travels
LANDMARKS_CATALOG = {
    # Israel / Jerusalén
    "גן החיות התנכי": (31.7454, 35.1764),
    "הזאולוגי": (31.7454, 35.1764),
    "נחל דרוך": (30.9322, 34.8219),
    "חוג משוטטים": (30.9322, 34.8219),
    "כפר מכביה": (32.0664, 34.8197),
    "נתבג": (32.0055, 34.8854),
    # Montenegro / Durmitor / Balkans
    "שמורת דורמיטור": (43.15, 19.0333),
    "דורמיטור": (43.15, 19.0333),
    "durmitor": (43.15, 19.0333),
    "אגם סקאדאר": (42.18, 19.14),
    "skadar": (42.18, 19.14),
    "דוברובניק": (42.6507, 18.0944),
    "dubrovnik": (42.6507, 18.0944),
    "קניון הטארה": (43.2084, 19.0769),
    "tara canyon": (43.2084, 19.0769),
    "מונטנגרו": (42.7087, 19.3744),
    "montenegro": (42.7087, 19.3744),
    # Italy / Roma / Firenze
    "pantheon": (41.8986, 12.4769),
    "colosseum": (41.8906, 12.4906),
    "coliseo": (41.8906, 12.4906),
    "roma": (41.9028, 12.4964),
    "rome": (41.9028, 12.4964),
    "florencia": (43.7781, 11.2454),
    "firenze": (43.7781, 11.2454),
    "pisa": (43.7228, 10.3948),
    "milan": (45.4885, 9.2102),
    "venecia": (45.4344, 12.3381),
    "venice": (45.4344, 12.3381),
    # Bosnia
    "sarajevo": (43.8563, 18.4131),
    "mostar": (43.3438, 17.8078),
    "jajce": (44.3419, 17.2703),
    "bihac": (44.8169, 15.8708),
    "bosnia": (44.2045, 17.8244),
    # Argentina
    "lago puelo": (-42.0625, -71.5975),
    "perito moreno": (-50.4689, -73.0300),
    "glaciar": (-50.4689, -73.0300),
    "chalten": (-49.3315, -72.8860),
    "calafate": (-50.3381, -72.2648),
    "bariloche": (-41.1335, -71.3103),
    "el bolson": (-41.9614, -71.5348),
    "iguazu": (-25.5972, -54.5766),
    "mendoza": (-32.8908, -68.8272),
    "salta": (-24.7821, -65.4232),
    "corrientes": (-27.4692, -58.8306),
    "catedral": (-41.1683, -71.4381),
    "cerro catedral": (-41.1683, -71.4381)
}

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

def load_file_properties(fp):
    """
    Reads physical file's keywords from IPTC or EXIF if present.
    """
    if not PIEXIF_AVAILABLE or not os.path.exists(fp):
        return ""
    
    tags_found = []
    try:
        # Load EXIF XPKeywords
        exif_dict = piexif.load(fp)
        kw = exif_dict.get('0th', {}).get(40094)
        if kw:
            tags_found.append(decode_xp_keywords(kw))
    except:
        pass
        
    try:
        # Scan raw bytes for IPTC windows-1255 Hebrew tags
        # and XMP UTF-8 tags (fast read)
        with open(fp, 'rb') as f:
            content = f.read(50000) # Read header portion
            
        # Check standard Hebrew landmark sequences
        for name in LANDMARKS_CATALOG.keys():
            # Check cp1255
            try:
                if name.encode('windows-1255') in content:
                    tags_found.append(name)
            except: pass
            # Check utf8
            if name.encode('utf-8') in content:
                tags_found.append(name)
    except:
        pass
        
    return " ".join(tags_found)

def main():
    apply_changes = "--apply" in sys.argv
    mode = "[EJECUCIÓN REAL]" if apply_changes else "[MODO SIMULACIÓN - DRY RUN]"
    
    print("=" * 80)
    print(f"  {mode} GEOLOCALIZACIÓN GENERALIZADA POR TAGS & FILENAMES")
    print("=" * 80)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # 1. Compile the unified strong tags map
        print("\nCompilando mapa de etiquetas fuertes...")
        unified_map = {}
        
        # Add landmarks catalog
        for name, coords in LANDMARKS_CATALOG.items():
            unified_map[name.lower().strip()] = {
                'lat': coords[0], 'lng': coords[1], 'source_name': name
            }
            
        # Add places from known_places table
        cursor = conn.execute("SELECT location_name, latitude, longitude FROM known_places WHERE location_name IS NOT NULL")
        for r in cursor.fetchall():
            name = r['location_name'].lower().strip()
            if name and len(name) > 3 and name not in unified_map:
                unified_map[name] = {
                    'lat': r['latitude'], 'lng': r['longitude'], 'source_name': r['location_name']
                }
                
        # Add bookings from initialBookings.json
        if os.path.exists(BOOKINGS_PATH):
            with open(BOOKINGS_PATH, 'r', encoding='utf-8') as f:
                bookings = json.load(f)
                for b in bookings:
                    loc = b.get('location_name') or b.get('location')
                    if loc:
                        name = loc.lower().strip()
                        if name and name not in unified_map:
                            unified_map[name] = {
                                'lat': b['latitude'], 'lng': b['longitude'], 'source_name': loc
                            }
                            
        print(f"Mapa de etiquetas compilado con éxito: {len(unified_map)} términos de búsqueda únicos.")
        
        # 2. Query all photos that are currently UNMAPPED (lat is NULL or 0.0)
        cursor = conn.execute("""
            SELECT id, file_path, filename, date_taken 
            FROM photos 
            WHERE lat IS NULL OR lat = 0.0 OR lat = ''
        """)
        unmapped_photos = cursor.fetchall()
        print(f"Total fotos en el catálogo sin geolocalizar (SIN_GEO): {len(unmapped_photos)}")
        
        geolocalized_photos = []
        
        print("\nProcesando fotos y buscando coincidencias de tags...")
        
        for idx, p in enumerate(unmapped_photos):
            pid = p['id']
            file_path = p['file_path']
            filename = p['filename'] or ""
            date_taken = p['date_taken']
            
            # Text to match
            text_to_search = []
            if filename:
                text_to_search.append(filename.lower())
            if file_path:
                text_to_search.append(file_path.lower())
                
            # If physical file exists, read its EXIF/IPTC properties
            if file_path and os.path.exists(file_path):
                physical_tags = load_file_properties(file_path)
                if physical_tags:
                    text_to_search.append(physical_tags.lower())
                    
            combined_text = " ".join(text_to_search)
            
            # Search for matching strong tags
            matched_tag_info = None
            for tag, info in unified_map.items():
                if tag in combined_text:
                    # We prefer the longest tag match first for higher precision!
                    if not matched_tag_info or len(tag) > len(matched_tag_info['tag']):
                        matched_tag_info = {
                            'tag': tag,
                            'lat': info['lat'],
                            'lng': info['lng'],
                            'source_name': info['source_name']
                        }
                        
            if matched_tag_info:
                lat = matched_tag_info['lat']
                lng = matched_tag_info['lng']
                loc_name = matched_tag_info['source_name']
                
                print(f"  -> [GEO-TAG] ID {pid}: {filename} -> Coincidencia: '{matched_tag_info['tag']}'")
                print(f"               Asignando: ({lat:.4f}, {lng:.4f}) | '{loc_name}'")
                
                geolocalized_photos.append({
                    'id': pid, 'lat': lat, 'lng': lng, 'location_name': loc_name,
                    'date_taken': date_taken, 'file_path': file_path
                })
                
        # Apply geocoding updates
        if geolocalized_photos:
            print(f"\nTotal fotos resueltas de forma determinista por tag: {len(geolocalized_photos)}")
            
            if apply_changes:
                conn.execute("BEGIN TRANSACTION;")
                for gp in geolocalized_photos:
                    conn.execute("""
                        UPDATE photos 
                        SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                            location_name = ?, location_source = 'VISION_LANDMARK',
                            confidence_score = 0.95
                        WHERE id = ?
                    """, (gp['lat'], gp['lng'], gp['lat'], gp['lng'], gp['location_name'], gp['id']))
                conn.commit()
                print("¡Ubicaciones registradas con éxito en la base de datos!")
                
            # 3. Spatiotemporal Neighborhood Propagation (Reverse-Geocoding)
            print("\n--- PROPAGACIÓN ESPACIO-TEMPORAL EN VECINDAD (+/- 45 MINUTOS) ---")
            propagated_count = 0
            
            propagated_ids = set()
            if apply_changes:
                conn.execute("BEGIN TRANSACTION;")
                
            for gp in geolocalized_photos:
                z_dt_str = gp['date_taken']
                if not z_dt_str: continue
                try:
                    z_dt = datetime.strptime(z_dt_str, "%Y-%m-%d %H:%M:%S")
                    date_prefix = z_dt_str[:10] # YYYY-MM-DD
                    
                    # Query other photos in the same year/month/day without GPS
                    cursor2 = conn.execute("""
                        SELECT id, date_taken, file_path 
                        FROM photos 
                        WHERE (lat IS NULL OR lat = 0.0 OR lat = '') 
                          AND date_taken IS NOT NULL 
                          AND date_taken LIKE ?
                    """, (date_prefix + "%",))
                    
                    candidates = cursor2.fetchall()
                    for cand in candidates:
                        cand_id = cand['id']
                        if cand_id in propagated_ids:
                            continue
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
                                    """, (gp['lat'], gp['lng'], gp['lat'], gp['lng'], gp['location_name'], cand_id))
                                propagated_ids.add(cand_id)
                        except: pass
                except: pass
                
            if apply_changes:
                conn.commit()
            print(f"\n¡Propagación completada! Fotos vecinas únicas que heredaron coordenadas: {len(propagated_ids)}")
            
        else:
            print("No se encontraron coincidencias de tags en las fotos sin geolocalizar.")
            
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
        print("    python apps/backend/scripts/generalized_tag_geocoding.py --apply")
        print("="*50)

if __name__ == '__main__':
    main()
