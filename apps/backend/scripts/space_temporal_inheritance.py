import os
import sys
import io
import json
import sqlite3
import glob
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
BOOKINGS_DIR = r"C:\Users\flier\GitHub\Reverse-Geocoding\apps\backend\src\data"
BOOKINGS_PATH = os.path.join(BOOKINGS_DIR, "initialBookings.json")

CITY_FALLBACK = {
    "buenos aires": (-34.6037, -58.3816),
    "rosario": (-32.9442, -60.6505),
    "bariloche": (-41.1335, -71.3103),
    "mendoza": (-32.8908, -68.8272),
    "salta": (-24.1858, -65.2995),
    "jujuy": (-24.1858, -65.2995),
    "iguazu": (-25.5972, -54.5766),
    "roma": (41.9029, 12.5056),
    "florencia": (43.7781, 11.2454),
    "milan": (45.4884, 9.2101),
    "sarajevo": (43.8563, 18.4131),
    "mostar": (43.3373, 17.815),
    "bled": (46.2528, 14.4533),
    "ljubljana": (46.0569, 14.5058),
}

def _fallback_coords(location_str):
    if not location_str:
        return None
    k = location_str.strip().lower()
    for name, coords in CITY_FALLBACK.items():
        if name in k or k in name:
            return coords
    return None

def infer_trip_name(country, title, path_or_source, start_date):
    if not start_date:
        return None
    year = start_date.split('-')[0]
    
    if country == 'Argentina':
        if year == '2011':
            return 'argentina-2011'
        return 'argentina-2025'
    elif country == 'Slovenia' or 'slovenia' in str(path_or_source).lower() or 'slovenia' in str(title).lower():
        return 'slovenia-2015'
    elif country == 'Bosnia' or 'bosnia' in str(path_or_source).lower() or 'bosnia' in str(title).lower() or 'bih' in str(title).lower():
        return 'bosnia-2023'
    elif country == 'Greece' or 'greece' in str(path_or_source).lower() or 'crete' in str(title).lower():
        return 'crete-2013'
    elif country in ('Croatia', 'Montenegro') or 'croatia' in str(path_or_source).lower() or 'montenegro' in str(path_or_source).lower():
        return 'croatia-montenegro-2010'
    elif country == 'Denmark' or 'denmark' in str(path_or_source).lower() or 'copenhagen' in str(title).lower():
        return 'denmark-2024'
    elif country == 'Italy' or 'italy' in str(path_or_source).lower() or 'italia' in str(title).lower():
        return 'italy-2023'
    elif country == 'Cyprus' or 'cyprus' in str(path_or_source).lower():
        return 'cyprus'
    
    # Generic text search
    low_title = str(title).lower()
    low_path = str(path_or_source).lower()
    
    if 'argentina' in low_title or 'argentina' in low_path:
        if '2011' in low_title or '2011' in low_path:
            return 'argentina-2011'
        return 'argentina-2025'
    if 'slovenia' in low_title or 'slovenia' in low_path or 'savica' in low_title or 'savica' in low_path:
        return 'slovenia-2015'
    if 'bosnia' in low_title or 'bosnia' in low_path or 'mostar' in low_title or 'mostar' in low_path:
        return 'bosnia-2023'
    if 'crete' in low_title or 'crete' in low_path or 'greece' in low_title:
        return 'crete-2013'
    if 'croatia' in low_title or 'croatia' in low_path or 'montenegro' in low_title or 'montenegro' in low_path:
        return 'croatia-montenegro-2010'
    if 'denmark' in low_title or 'denmark' in low_path or 'copenhagen' in low_title or 'copenhagen' in low_path:
        return 'denmark-2024'
    if 'italy' in low_title or 'italy' in low_path or 'italia' in low_title or 'italia' in low_path or 'roma' in low_title or 'roma' in low_path:
        return 'italy-2023'
    if 'cyprus' in low_title or 'cyprus' in low_path:
        return 'cyprus'
        
    return None

def extract_bookings():
    bookings = []
    
    # 1. Load from travel_bookings_import_1784659840011.json
    import_path = r"C:\Users\flier\GitHub\Reverse-Geocoding\apps\frontend\photo-import-output\travel_bookings_import_1784659840011.json"
    if os.path.exists(import_path):
        with open(import_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                lat = item.get('_lat')
                lng = item.get('_lng')
                if lat is None or lng is None or lat == 0.0 or lng == 0.0:
                    continue
                    
                start_date = item.get('startDate')
                if not start_date:
                    continue
                end_date = item.get('endDate') or start_date
                
                title = item.get('title') or item.get('summary') or 'Reserva'
                location = item.get('location') or title
                country = item.get('_country')
                
                trip_name = infer_trip_name(country, title, item.get('fileName'), start_date)
                if not trip_name:
                    continue
                    
                bookings.append({
                    'id': item.get('id'),
                    'trip_name': trip_name,
                    'date_start': start_date,
                    'date_end': end_date,
                    'startDate': start_date,
                    'endDate': end_date,
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'coordinates': {'lat': float(lat), 'lng': float(lng)},
                    'location_name': location,
                    'location': location
                })
                
    # 2. Load from data/vouchers/2026-09/*.json
    vouchers_pattern = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\vouchers\2026-09\*.json"
    v_paths = glob.glob(vouchers_pattern)
    for vp in v_paths:
        try:
            with open(vp, 'r', encoding='utf-8') as f:
                d = json.load(f)
                p_info = d.get('parsed', {})
                if not p_info or not p_info.get('isTravelDocument'):
                    continue
                    
                start_date = p_info.get('startDate')
                if not start_date:
                    continue
                end_date = p_info.get('endDate') or start_date
                
                coords = p_info.get('coordinates')
                lat, lng = None, None
                if coords and coords.get('lat') is not None:
                    lat = coords.get('lat')
                    lng = coords.get('lng')
                else:
                    loc = p_info.get('location') or p_info.get('title')
                    if loc:
                        fb = _fallback_coords(loc)
                        if fb:
                            lat, lng = fb
                            
                if lat is None or lng is None or lat == 0.0 or lng == 0.0:
                    continue
                    
                title = p_info.get('title') or p_info.get('summary') or 'Voucher'
                location = p_info.get('location') or title
                
                # Infer country based on coordinate box or text
                country = None
                if lat > 0:
                    if 12.0 <= lng <= 14.0:
                        country = 'Italy'
                    elif 13.5 <= lng <= 15.5:
                        country = 'Slovenia'
                    elif 15.0 <= lng <= 19.5:
                        country = 'Bosnia'
                    elif 20.0 <= lng <= 25.0:
                        country = 'Greece'
                    elif 9.0 <= lng <= 15.0:
                        country = 'Denmark'
                else:
                    if -75.0 <= lng <= -55.0:
                        country = 'Argentina'
                        
                trip_name = infer_trip_name(country, title, vp, start_date)
                if not trip_name:
                    continue
                    
                bid = f"voucher-{os.path.basename(vp).replace('.json', '')}"
                bookings.append({
                    'id': bid,
                    'trip_name': trip_name,
                    'date_start': start_date,
                    'date_end': end_date,
                    'startDate': start_date,
                    'endDate': end_date,
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'coordinates': {'lat': float(lat), 'lng': float(lng)},
                    'location_name': location,
                    'location': location
                })
        except Exception:
            pass
            
    unique_bookings = []
    seen_ids = set()
    for b in bookings:
        if b['id'] not in seen_ids:
            seen_ids.add(b['id'])
            unique_bookings.append(b)
            
    return unique_bookings

def parse_date_only(dt_str):
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    if len(dt_str) >= 10:
        date_part = dt_str[:10].replace(':', '-').replace('/', '-')
        if len(date_part) == 10 and date_part[0].isdigit() and date_part[4] == '-' and date_part[7] == '-':
            return date_part
    return None

def main():
    print("=== INICIANDO MOTOR DE HERENCIA ESPACIO-TEMPORAL ===")
    
    # 1. Consolidación de Reservas (initialBookings.json)
    print("\nExtracting and consolidating bookings from import files and vouchers...")
    bookings = extract_bookings()
    print(f"Total bookings consolidated: {len(bookings)}")
    
    # Sort bookings by duration ascending (shorter more specific events first)
    def get_duration(b):
        try:
            s = datetime.strptime(b['date_start'], '%Y-%m-%d')
            e = datetime.strptime(b['date_end'], '%Y-%m-%d')
            return (e - s).days
        except Exception:
            return 9999
            
    bookings.sort(key=get_duration)
    
    # Save to initialBookings.json
    os.makedirs(BOOKINGS_DIR, exist_ok=True)
    with open(BOOKINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(bookings, f, ensure_ascii=False, indent=2)
    print(f"Consolidado de reservas guardado con éxito en: {BOOKINGS_PATH}")
    
    # 2. Motor de Herencia Espacio-Temporal
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    try:
        # Fetch all photos without valid GPS coordinates (latitude IS NULL or 0.0)
        cursor = conn.execute("""
            SELECT id, date_taken, file_path 
            FROM photos 
            WHERE (lat IS NULL OR lat = 0.0 OR lat = '') 
              AND date_taken IS NOT NULL 
              AND date_taken != ''
        """)
        photos_to_inherit = cursor.fetchall()
        print(f"\nTotal fotos sin coordenadas con fecha para analizar: {len(photos_to_inherit)}")
        
        inherited_count = 0
        conn.execute("BEGIN TRANSACTION;")
        
        for pid, date_taken, path in photos_to_inherit:
            photo_date = parse_date_only(date_taken)
            if not photo_date:
                continue
                
            # Find matching booking
            matched_booking = None
            for b in bookings:
                if b['date_start'] <= photo_date <= b['date_end']:
                    matched_booking = b
                    break
                    
            if matched_booking:
                lat = matched_booking['latitude']
                lng = matched_booking['longitude']
                loc_name = matched_booking['location_name']
                trip_name = matched_booking['trip_name']
                bid = matched_booking['id']
                
                # Update the record
                conn.execute("""
                    UPDATE photos 
                    SET lat = ?, lng = ?, latitude = ?, longitude = ?, 
                        location_name = ?, location_source = 'VOUCHER_INHERITANCE', 
                        booking_id = ?, trip_name = ?
                    WHERE id = ?
                """, (lat, lng, lat, lng, loc_name, bid, trip_name, pid))
                inherited_count += 1
                
        conn.commit()
        print(f"¡Sincronización de herencia finalizada! Fotos que heredaron ubicación: {inherited_count}")
        
        # 3. Reporte de Resultados
        print("\n=== 3. REPORTE DE RESULTADOS DE HERENCIA ===")
        total_photos = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        
        # Count by location_source
        sources = conn.execute("""
            SELECT COALESCE(location_source, 'SIN_GEO'), COUNT(*) 
            FROM photos 
            GROUP BY COALESCE(location_source, 'SIN_GEO')
        """).fetchall()
        
        print(f"Total fotos en el catálogo consolidado: {total_photos}")
        for src, count in sources:
            print(f"  - {src:<20}: {count} ({count/total_photos*100:.2f}%)")
            
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Ocurrió un fallo en el motor de herencia: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
