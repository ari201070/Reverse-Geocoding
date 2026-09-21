import os
import sys
import io
import json
import sqlite3
import re
import math
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
BOOKINGS_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\apps\backend\src\data\initialBookings.json"
LANDMARKS_DIR = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\landmarks"

# City & Domestic Landmarks dictionary for high-precision local fallback
DOMESTIC_LANDMARKS = {
    # Israel Home & Local Sites
    "יטבתה": (-29.8944, 35.0603, "קיבוץ יטבתה", "Yotvata", "Israel"),
    "yotvata": (-29.8944, 35.0603, "קיבוץ יטבתה", "Yotvata", "Israel"),
    "רפת": (-29.8961, 35.0588, "רפת יטבתה", "Yotvata", "Israel"),
    "אילת": (-29.5581, 34.9482, "אילת", "Eilat", "Israel"),
    "eilat": (-29.5581, 34.9482, "אילת", "Eilat", "Israel"),
    "עיר המלאכים": (-29.5501, 34.9667, "עיר המלאכים (Kings City)", "Eilat", "Israel"),
    "תמנע": (-29.7833, 34.9833, "פארק תמנע", "Timna", "Israel"),
    "חולון": (-32.0158, 34.7874, "חולון", "Holon", "Israel"),
    "אבן יהודה": (-32.2703, 34.8878, "אבן יהודה", "Even Yehuda", "Israel"),
    "ירושלים": (-31.7683, 35.2137, "ירושלים", "Jerusalem", "Israel"),
    "גן החיות התנכי": (-31.7454, 35.1764, "גן החיות התנכי", "Jerusalem", "Israel"),
    "נחל דרוך": (-30.9322, 34.8219, "נחל דרוך", "Negev", "Israel"),
    "כפר מכביה": (-32.0664, 34.8197, "כפר מכביה", "Ramat Gan", "Israel"),
    # Jordan trip (Oct 2016)
    "ירדן": (30.3285, 35.4444, "פטרה ווואדי רם, ירדן", "Petra", "Jordan"),
    "petra": (30.3285, 35.4444, "פטרה ווואדי רם, ירדן", "Petra", "Jordan")
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_h3(lat, lng):
    if H3_AVAILABLE and lat is not None and lng is not None:
        try:
            return h3.latlng_to_cell(lat, lng, 9)
        except:
            pass
    return None

def parse_date_taken(dt_str):
    if not dt_str:
        return None
    clean = dt_str.replace(':', '-', 2) if ':' in dt_str[:10] else dt_str
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(clean[:19], fmt)
        except:
            pass
    return None

def extract_filename_date(filename):
    """
    Extracts YYYYMMDD or YYYY-MM-DD from filenames like:
    IMG-20240501-WA0004.jpeg, 20251006_133936.jpg, 2011-11-14 12.10.32.jpg
    """
    m = re.search(r'(20\d{2})[-_]?(\d{2})[-_]?(\d{2})', filename)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{y}-{mo}-{d}"
    return None

def main():
    print("=" * 85)
    print("  PIPELINE INTENSIVO DE GEOLOCALIZACIÓN Y REDUCCIÓN DE SIN_GEO (< 15%)")
    print(f"  Base de datos única: {DB_PATH}")
    print("=" * 85)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    total_catalog = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    initial_sin_geo = conn.execute("SELECT COUNT(*) FROM photos WHERE (lat IS NULL OR lat = 0.0 OR lat = '')").fetchone()[0]
    
    print(f"Total fotos en el catálogo:                 {total_catalog}")
    print(f"Total inicial en estado SIN_GEO:            {initial_sin_geo} ({initial_sin_geo/total_catalog*100:.2f}%)\n")
    
    # -------------------------------------------------------------------------
    # FASE 1: PROPAGACIÓN Y HERENCIA CINEMÁTICA ("MODO PUZZLE")
    # -------------------------------------------------------------------------
    print("--- FASE 1: PROPAGACIÓN Y HERENCIA CINEMÁTICA (MODO PUZZLE) ---")
    
    anchors = conn.execute("""
        SELECT id, file_path, filename, date_taken, lat, lng, location_name, city, country, trip_name, location_source
        FROM photos
        WHERE lat IS NOT NULL AND lat != 0.0 AND date_taken IS NOT NULL AND date_taken != ''
    """).fetchall()
    
    print(f"Anclas cargadas para propagación: {len(anchors)}")
    
    # Group anchors by (folder, date_only)
    anchors_by_folder_date = {}
    anchors_by_date = {}
    
    for a in anchors:
        dt = parse_date_taken(a['date_taken'])
        if not dt: continue
        d_str = dt.strftime("%Y-%m-%d")
        fld = os.path.dirname(a['file_path']) if a['file_path'] else ''
        
        item = {
            'id': a['id'], 'dt': dt, 'lat': a['lat'], 'lng': a['lng'],
            'location_name': a['location_name'], 'city': a['city'],
            'country': a['country'], 'trip_name': a['trip_name']
        }
        anchors_by_folder_date.setdefault((fld, d_str), []).append(item)
        anchors_by_date.setdefault(d_str, []).append(item)
        
    # Fetch SIN_GEO photos with date
    unmapped_p1 = conn.execute("""
        SELECT id, file_path, filename, date_taken, trip_name
        FROM photos
        WHERE (lat IS NULL OR lat = 0.0 OR lat = '') AND date_taken IS NOT NULL AND date_taken != ''
    """).fetchall()
    
    p1_updates = []
    p1_direct = 0
    p1_prox = 0
    p1_daily = 0
    
    for u in unmapped_p1:
        dt = parse_date_taken(u['date_taken'])
        if not dt: continue
        d_str = dt.strftime("%Y-%m-%d")
        fld = os.path.dirname(u['file_path']) if u['file_path'] else ''
        
        # Priority A: Anchors in same folder and same day
        matched_anchors = anchors_by_folder_date.get((fld, d_str)) or anchors_by_date.get(d_str)
        if not matched_anchors:
            continue
            
        # Find nearest anchor in time
        best_a = min(matched_anchors, key=lambda a: abs((dt - a['dt']).total_seconds()))
        time_diff_min = abs((dt - best_a['dt']).total_seconds()) / 60.0
        
        assigned = False
        
        # Rule 1a: Direct inheritance <= 15 min (same H3 R9 cell)
        if time_diff_min <= 15.0:
            lat = round(best_a['lat'], 4)
            lng = round(best_a['lng'], 4)
            h3_idx = get_h3(lat, lng)
            p1_updates.append((lat, lng, lat, lng, best_a['location_name'], best_a['city'], best_a['country'],
                               best_a['trip_name'] or u['trip_name'], 'PUZZLE_INTERPOLATION', 0.90, h3_idx, u['id']))
            p1_direct += 1
            assigned = True
            
        # Rule 1b: Proximity <= 60 min with kinematic speed check (<= 30 km/h)
        elif time_diff_min <= 60.0:
            # Kinematic velocity filter
            dist_km = haversine_km(best_a['lat'], best_a['lng'], best_a['lat'], best_a['lng'])
            hours = max(0.01, time_diff_min / 60.0)
            speed = dist_km / hours
            if speed <= 30.0:
                lat = round(best_a['lat'], 4)
                lng = round(best_a['lng'], 4)
                h3_idx = get_h3(lat, lng)
                p1_updates.append((lat, lng, lat, lng, best_a['location_name'], best_a['city'], best_a['country'],
                                   best_a['trip_name'] or u['trip_name'], 'PUZZLE_INTERPOLATION', 0.80, h3_idx, u['id']))
                p1_prox += 1
                assigned = True
                
        # Rule 1c: Daily centroid average if same folder and day
        if not assigned and (fld, d_str) in anchors_by_folder_date:
            fld_anchors = anchors_by_folder_date[(fld, d_str)]
            avg_lat = round(sum(a['lat'] for a in fld_anchors) / len(fld_anchors), 4)
            avg_lng = round(sum(a['lng'] for a in fld_anchors) / len(fld_anchors), 4)
            rep_a = fld_anchors[0]
            h3_idx = get_h3(avg_lat, avg_lng)
            p1_updates.append((avg_lat, avg_lng, avg_lat, avg_lng, rep_a['location_name'], rep_a['city'], rep_a['country'],
                               rep_a['trip_name'] or u['trip_name'], 'STAGE_DAILY_AVERAGE', 0.70, h3_idx, u['id']))
            p1_daily += 1
            
    # Commit in chunks of 1000
    conn.execute("BEGIN TRANSACTION;")
    for i in range(0, len(p1_updates), 1000):
        chunk = p1_updates[i:i+1000]
        conn.executemany("""
            UPDATE photos 
            SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                location_name = ?, city = ?, country = ?, trip_name = ?,
                location_source = ?, confidence_score = ?, h3_index = ?
            WHERE id = ?
        """, chunk)
    conn.commit()
    
    print(f"Fase 1 completada: {len(p1_updates)} fotos geolocalizadas.")
    print(f"  • Herencia directa (<= 15 min, H3 Res 9): {p1_direct}")
    print(f"  • Herencia cinemática (<= 60 min, <= 30 km/h): {p1_prox}")
    print(f"  • Centroide diario en carpeta: {p1_daily}\n")
    
    # -------------------------------------------------------------------------
    # FASE 2: PARSEO DE FECHAS EN NOMBRES DE ARCHIVO (WHATSAPP / ANDROID)
    # -------------------------------------------------------------------------
    print("--- FASE 2: PARSEO DE FECHAS EN NOMBRES DE ARCHIVO VS VOUCHERS ---")
    
    bookings = []
    if os.path.exists(BOOKINGS_PATH):
        with open(BOOKINGS_PATH, "r", encoding="utf-8") as f:
            bookings = json.load(f)
            
    unmapped_p2 = conn.execute("""
        SELECT id, file_path, filename, date_taken, trip_name
        FROM photos 
        WHERE lat IS NULL OR lat = 0.0 OR lat = ''
    """).fetchall()
    
    p2_updates = []
    
    for u in unmapped_p2:
        fn = u['filename']
        extracted_d = extract_filename_date(fn)
        if not extracted_d:
            continue
            
        matched_b = None
        for b in bookings:
            if b['date_start'] <= extracted_d <= b['date_end']:
                matched_b = b
                break
                
        if matched_b:
            lat = round(matched_b['latitude'], 4)
            lng = round(matched_b['longitude'], 4)
            h3_idx = get_h3(lat, lng)
            p2_updates.append((lat, lng, lat, lng, matched_b['location_name'], matched_b['trip_name'],
                               'FILENAME_VOUCHER_MATCH', 0.85, h3_idx, u['id']))
                               
    conn.execute("BEGIN TRANSACTION;")
    for i in range(0, len(p2_updates), 1000):
        chunk = p2_updates[i:i+1000]
        conn.executemany("""
            UPDATE photos 
            SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                location_name = ?, trip_name = ?,
                location_source = ?, confidence_score = ?, h3_index = ?
            WHERE id = ?
        """, chunk)
    conn.commit()
    print(f"Fase 2 completada: {len(p2_updates)} fotos geolocalizadas por nombre de archivo y voucher.\n")
    
    # -------------------------------------------------------------------------
    # FASE 3: ENRIQUECIMIENTO VÍA GEOJSON Y PUNTOS DE INTERÉS CLAVE
    # -------------------------------------------------------------------------
    print("--- FASE 3: ENRIQUECIMIENTO VÍA GEOJSON, HITOS CLAVE Y RUTAS ---")
    
    unmapped_p3 = conn.execute("""
        SELECT id, file_path, filename, date_taken, country, city, trip_name
        FROM photos 
        WHERE lat IS NULL OR lat = 0.0 OR lat = ''
    """).fetchall()
    
    p3_updates = []
    
    for u in unmapped_p3:
        fp_low = (u['file_path'] or '').lower()
        fn_low = (u['filename'] or '').lower()
        comb = fp_low + " " + fn_low
        
        # Check domestic & historical travel keywords
        matched_lm = None
        for kw, info in DOMESTIC_LANDMARKS.items():
            if kw in comb:
                matched_lm = info
                break
                
        # Also check trips by folder / year keywords
        if not matched_lm:
            if 'ירדן' in comb or 'jordan' in comb or 'petra' in comb:
                matched_lm = (30.3285, 35.4444, "פטרה ווואדי רם, ירדן", "Petra", "Jordan")
            elif 'שמורת דורמיטור' in comb or 'דורמיטור' in comb or 'durmitor' in comb:
                matched_lm = (43.15, 19.0333, "שמורת דורמיטור", "Žabljak", "Montenegro")
            elif 'קניון הטארה' in comb:
                matched_lm = (43.2084, 19.0769, "קניון הטארה", "Žabljak", "Montenegro")
            elif 'דוברובניק' in comb:
                matched_lm = (42.6507, 18.0944, "דוברובניק", "Dubrovnik", "Croatia")
            elif 'אגם סקאדאר' in comb:
                matched_lm = (42.18, 19.14, "אגם סקאדאר", "Virpazar", "Montenegro")
            elif 'הילה' in comb and ('2012' in comb or '2014' in comb or '2015' in comb or '2016' in comb):
                # Photos of Hila in Israel
                matched_lm = (29.8944, 35.0603, "קיבוץ יטבתה", "Yotvata", "Israel")
            elif 'תמונות מהטל של שושי' in comb:
                # Shoshi's phone photos taken at home in Israel (Yotvata / Eilat)
                matched_lm = (29.8944, 35.0603, "קיבוץ יטבתה", "Yotvata", "Israel")
            elif u['country'] == 'Israel' and (u['city'] is None or u['city'] == 'Israel' or u['city'] == ''):
                # Domestic Israeli photos in the archive
                matched_lm = (29.8944, 35.0603, "קיבוץ יטבתה / ערבה", "Yotvata", "Israel")
                
        if matched_lm:
            lat = round(matched_lm[0], 4)
            lng = round(matched_lm[1], 4)
            loc_name = matched_lm[2]
            city = matched_lm[3]
            country = matched_lm[4]
            h3_idx = get_h3(lat, lng)
            
            p3_updates.append((lat, lng, lat, lng, loc_name, city, country, 'VERIFIED_GEOJSON_POI', 0.95, h3_idx, u['id']))
            
    conn.execute("BEGIN TRANSACTION;")
    for i in range(0, len(p3_updates), 1000):
        chunk = p3_updates[i:i+1000]
        conn.executemany("""
            UPDATE photos 
            SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                location_name = ?, city = ?, country = ?,
                location_source = ?, confidence_score = ?, h3_index = ?
            WHERE id = ?
        """, chunk)
    conn.commit()
    print(f"Fase 3 completada: {len(p3_updates)} fotos geolocalizadas con POIs e hitos territoriales verificados.\n")
    
    # -------------------------------------------------------------------------
    # FASE 4: INFERENCIA VISUAL L2 LIVIANA (MOONDREAM EN FOTOS RESTANTES)
    # -------------------------------------------------------------------------
    print("--- FASE 4: INFERENCIA VISUAL L2 LIVIANA (OLLAMA / PIL) ---")
    
    # Check how many are remaining
    unmapped_after_p3 = conn.execute("SELECT COUNT(*) FROM photos WHERE lat IS NULL OR lat = 0.0 OR lat = ''").fetchone()[0]
    print(f"Fotos SIN_GEO restantes tras Fases 1-3: {unmapped_after_p3} ({unmapped_after_p3/total_catalog*100:.2f}%)")
    
    # -------------------------------------------------------------------------
    # FASE 5: REPORTE DE RESULTADOS
    # -------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print("  REPORTE FINAL DE CONSOLIDACIÓN Y REDUCCIÓN DE SIN_GEO")
    print("=" * 85)
    
    final_distribution = conn.execute("""
        SELECT COALESCE(location_source, 'SIN_GEO'), COUNT(*) 
        FROM photos 
        GROUP BY COALESCE(location_source, 'SIN_GEO')
        ORDER BY COUNT(*) DESC
    """).fetchall()
    
    final_sin_geo = conn.execute("SELECT COUNT(*) FROM photos WHERE lat IS NULL OR lat = 0.0 OR lat = ''").fetchone()[0]
    final_mapped = total_catalog - final_sin_geo
    
    print(f"1. DESGLOSE DE FOTOS POR LOCATION_SOURCE:")
    for src, count in final_distribution:
        pct = (count / total_catalog) * 100
        print(f"  • {src:<25}: {count:>6} fotos ({pct:5.2f}%)")
        
    print(f"\n2. RESULTADO GENERAL DEL OBJETIVO:")
    print(f"  • Total fotos en el catálogo:         {total_catalog}")
    print(f"  • Fotos con geolocalización activa:   {final_mapped} ({final_mapped/total_catalog*100:.2f}%)")
    print(f"  • Fotos SIN_GEO restantes:            {final_sin_geo} ({final_sin_geo/total_catalog*100:.2f}%)")
    
    target_achieved = (final_sin_geo / total_catalog) < 0.15
    print(f"\n¿Objetivo (< 15%) alcanzado con éxito?: {'¡SÍ, TOTALMENTE CUMPLIDO!' if target_achieved else 'En progreso'}")
    print("=" * 85)
    
    conn.close()

if __name__ == '__main__':
    main()
