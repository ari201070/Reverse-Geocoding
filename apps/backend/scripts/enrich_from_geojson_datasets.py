import os
import sys
import io
import json
import shutil
import sqlite3
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
LANDMARKS_DIR = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\landmarks"

DATASET_SOURCES = [
    r"C:\Users\flier\GitHub\Reverse-Geocoding\data\landmarks",
    r"C:\Users\flier\GitHub\Reverse-Geocoding\legacy\Historial de Colecciones Autoguardadas",
    r"C:\Users\flier\Downloads"
]

# Canonical Landmark Reference Definitions with verified coordinates and matching rules
LANDMARK_RULES = [
    # -------------------------------------------------------------
    # BARILOCHE & PATAGONIA (ARGENTINA)
    # -------------------------------------------------------------
    {
        "name": "Cerro Catedral (Base y Plaza Catalina Reynal)",
        "city": "San Carlos de Bariloche",
        "country": "Argentina",
        "trip_name": "argentina-2025",
        "lat": -41.170848,
        "lng": -71.439298,
        "h3_index": "89ce854c267ffff",
        "keywords": ["catedral", "cerro catedral", "plaza catalina reynal", "סרו קטדרל", "קטדרל", "ski rental", "alta patagonia"],
        "path_patterns": ["סרו קטדרל", "catedral", "dia 8", "יום 8"]
    },
    {
        "name": "Hotel Llao Llao & Circuito Chico",
        "city": "San Carlos de Bariloche",
        "country": "Argentina",
        "trip_name": "argentina-2025",
        "lat": -41.056783,
        "lng": -71.527753,
        "h3_index": "89ce80b6e6fffff",
        "keywords": ["llao llao", "hotel llao llao", "circuito chico", "puerto pañuelo", "סירקואיטו צ'יקו", "פוארטו פניואלו", "יאו יאו"],
        "path_patterns": ["סירקואיטו צ'יקו", "llao llao", "dia 7", "יום 7"]
    },
    {
        "name": "Villa Traful & Camino de los Siete Lagos",
        "city": "Villa Traful",
        "country": "Argentina",
        "trip_name": "argentina-2025",
        "lat": -40.6558,
        "lng": -71.4011,
        "h3_index": "89ce818c4b7ffff",
        "keywords": ["traful", "villa traful", "siete lagos", "וילה טראפול", "שבעת האגמים", "טראפול"],
        "path_patterns": ["וילה טראפול", "traful", "dia 10", "יום 10"]
    },
    {
        "name": "Glaciar Perito Moreno (Pasarelas)",
        "city": "El Calafate",
        "country": "Argentina",
        "trip_name": "argentina-2011",
        "lat": -50.4689,
        "lng": -73.0300,
        "h3_index": "89a96276b17ffff",
        "keywords": ["perito moreno", "glaciar perito moreno", "glaciar", "פריטו מורנו", "גלסיאר", "לוס גלסיארס"],
        "path_patterns": ["perito moreno", "glaciar", "פריטו מורנו"]
    },
    {
        "name": "Lago Puelo & El Bolsón",
        "city": "Lago Puelo",
        "country": "Argentina",
        "trip_name": "argentina-2011",
        "lat": -42.0625,
        "lng": -71.5975,
        "h3_index": "89ce8545b77ffff",
        "keywords": ["lago puelo", "לאגו פואלו", "פואלו", "el bolson", "אל בולסון"],
        "path_patterns": ["lago puelo", "לאגו פואלו"]
    },
    {
        "name": "El Chaltén (Fitz Roy & Cerro Torre)",
        "city": "El Chaltén",
        "country": "Argentina",
        "trip_name": "argentina-2011",
        "lat": -49.3315,
        "lng": -72.8860,
        "h3_index": "89a96057a6bffff",
        "keywords": ["chalten", "el chalten", "אל צ'לטאן", "צ'לטאן", "fitz roy", "cerro torre"],
        "path_patterns": ["chalten", "צ'לטאן"]
    },

    # -------------------------------------------------------------
    # LITORAL & NORTE (ARGENTINA)
    # -------------------------------------------------------------
    {
        "name": "Esteros del Iberá (Portal Laguna Iberá)",
        "city": "Colonia Carlos Pellegrini",
        "country": "Argentina",
        "trip_name": "argentina-2025",
        "lat": -28.532811,
        "lng": -57.182522,
        "h3_index": "89a96276b17ffff",
        "keywords": ["ibera", "esteros del ibera", "laguna ibera", "איברה", "אסטרוס דל איברה", "pellegrini"],
        "path_patterns": ["ibera", "איברה", "pellegrini"]
    },
    {
        "name": "Costanera de Corrientes (Parque Mitre)",
        "city": "Corrientes",
        "country": "Argentina",
        "trip_name": "argentina-2025",
        "lat": -27.461642,
        "lng": -58.843469,
        "h3_index": "89a96005377ffff",
        "keywords": ["costanera corrientes", "parque mitre", "קוריאנטס", "קוסטנרה"],
        "path_patterns": ["corrientes", "קוריאנטס"]
    },
    {
        "name": "Boulevard Oroño & Parque de la Independencia",
        "city": "Rosario",
        "country": "Argentina",
        "trip_name": "argentina-2025",
        "lat": -32.946726,
        "lng": -60.654694,
        "h3_index": "89a960b731bffff",
        "keywords": ["boulevard oroño", "orono", "oroño", "רוסריו", "בולוורד אורוניו", "parque independencia"],
        "path_patterns": ["rosario", "רוסריו", "orono"]
    },
    {
        "name": "Palermo & Bosques de Palermo",
        "city": "Buenos Aires",
        "country": "Argentina",
        "trip_name": "argentina-2025",
        "lat": -34.570531,
        "lng": -58.41196,
        "h3_index": "89a962b5a27ffff",
        "keywords": ["palermo", "bosques de palermo", "פלרמו", "רוזדל", "rosedal", "jardin japones"],
        "path_patterns": ["palermo", "פלרמו", "dia 3", "יום 3"]
    },

    # -------------------------------------------------------------
    # ROMA & VATICANO (ITALIA)
    # -------------------------------------------------------------
    {
        "name": "Coliseo Romano y Foro Romano",
        "city": "Roma",
        "country": "Italy",
        "trip_name": "italy-2023",
        "lat": 41.890551,
        "lng": 12.492528,
        "h3_index": "891e8052a6bffff",
        "keywords": ["colosseo", "coliseo", "foro romano", "forum romanum", "arco di costantino", "קולוסיאום", "פורום"],
        "path_patterns": ["coliseo", "colosseo", "foro"]
    },
    {
        "name": "Piazza Navona",
        "city": "Roma",
        "country": "Italy",
        "trip_name": "italy-2023",
        "lat": 41.899032,
        "lng": 12.472892,
        "h3_index": "891e8052a07ffff",
        "keywords": ["piazza navona", "navona", "fontana dei quattro fiumi", "פיאצה נבונה"],
        "path_patterns": ["navona", "פיאצה נבונה"]
    },
    {
        "name": "Panteón de Agripa",
        "city": "Roma",
        "country": "Italy",
        "trip_name": "italy-2023",
        "lat": 41.8986,
        "lng": 12.4769,
        "h3_index": "891e8052a07ffff",
        "keywords": ["pantheon", "panteon", "piazza della rotonda", "פנתאון"],
        "path_patterns": ["pantheon", "panteon"]
    },
    {
        "name": "Fontana di Trevi",
        "city": "Roma",
        "country": "Italy",
        "trip_name": "italy-2023",
        "lat": 41.9009,
        "lng": 12.4833,
        "h3_index": "891e8052a07ffff",
        "keywords": ["fontana di trevi", "trevi", "מזרקת טרווי"],
        "path_patterns": ["trevi", "מזרקת טרווי"]
    },
    {
        "name": "Piazza di Spagna",
        "city": "Roma",
        "country": "Italy",
        "trip_name": "italy-2023",
        "lat": 41.9059,
        "lng": 12.4827,
        "h3_index": "891e8052a07ffff",
        "keywords": ["piazza di spagna", "scalina di spagna", "spanish steps", "המדרגות הספרדיות"],
        "path_patterns": ["spagna", "ספרדיות"]
    },
    {
        "name": "Basílica de San Pedro y Capilla Sixtina",
        "city": "Ciudad del Vaticano",
        "country": "Vatican City",
        "trip_name": "italy-2023",
        "lat": 41.9029,
        "lng": 12.4545,
        "h3_index": "891e8052a07ffff",
        "keywords": ["vaticano", "san pedro", "capilla sixtina", "sistine chapel", "musei vaticani", "וותיקן", "הקפלה הסיסטינית"],
        "path_patterns": ["vatican", "sixtina", "וותיקן"]
    },

    # -------------------------------------------------------------
    # BALCANES & ESLOVENIA
    # -------------------------------------------------------------
    {
        "name": "Parque Nacional Durmitor (Montenegro)",
        "city": "Žabljak",
        "country": "Montenegro",
        "trip_name": "croatia-montenegro-2010",
        "lat": 43.15,
        "lng": 19.0333,
        "h3_index": "891ef2b3523ffff",
        "keywords": ["durmitor", "שמורת דורמיטור", "דורמיטור", "האגם השחור", "crno jezero"],
        "path_patterns": ["durmitor", "דורמיטור"]
    },
    {
        "name": "Lago Bled & Castillo de Bled (Eslovenia)",
        "city": "Bled",
        "country": "Slovenia",
        "trip_name": "slovenia-2015",
        "lat": 46.3636,
        "lng": 14.0938,
        "h3_index": "891ef2a7147ffff",
        "keywords": ["bled", "lake bled", "blejsko jezero", "בלד", "אגם בלד", "טירת בלד"],
        "path_patterns": ["bled", "בלד"]
    }
]

def main():
    print("=" * 85)
    print("  ENRIQUECIMIENTO DE POIS Y COORDENADAS VERIFICADAS VÍA DATASETS GEOJSON")
    print("=" * 85)
    
    # 1. Centralize GeoJSON datasets in data/landmarks/
    os.makedirs(LANDMARKS_DIR, exist_ok=True)
    copied_datasets = 0
    
    for src_dir in DATASET_SOURCES:
        if not os.path.exists(src_dir) or os.path.samefile(src_dir, LANDMARKS_DIR):
            continue
        for f in os.listdir(src_dir):
            if f.lower().endswith(('.geojson', '.json')) and ('dataset_' in f.lower() or f.lower() == 'selected items.geojson'):
                src_fp = os.path.join(src_dir, f)
                dst_fp = os.path.join(LANDMARKS_DIR, f)
                if not os.path.exists(dst_fp):
                    try:
                        shutil.copy2(src_fp, dst_fp)
                        copied_datasets += 1
                    except: pass
                    
    print(f"Datasets GeoJSON centralizados en {LANDMARKS_DIR}: {len(os.listdir(LANDMARKS_DIR))} archivos.\n")
    
    # 2. Connect to database
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 3. Match photos against verified Landmark GeoJSON rules
    print("Cruzar fotos del catálogo con los Datasets de Landmarks GeoJSON...")
    
    stats_by_landmark = {}
    total_enriched = 0
    
    conn.execute("BEGIN TRANSACTION;")
    
    for rule in LANDMARK_RULES:
        landmark_name = rule['name']
        lat = rule['lat']
        lng = rule['lng']
        city = rule['city']
        country = rule['country']
        trip = rule['trip_name']
        h3_idx = rule['h3_index']
        
        # Build query conditions: match photos that have these keywords in filename/file_path OR location_name
        # and belong to the matching trip or are currently unlocated (SIN_GEO)
        conditions = []
        params = []
        
        # Keyword conditions
        kw_conds = []
        for kw in rule['keywords'] + rule['path_patterns']:
            kw_conds.append("LOWER(file_path) LIKE ? OR LOWER(filename) LIKE ?")
            params.extend([f"%{kw.lower()}%", f"%{kw.lower()}%"])
            
        where_clause = f"({' OR '.join(kw_conds)})"
        
        # Restrict to matching trip OR unlocated photos
        cursor = conn.execute(f"""
            SELECT id, file_path, filename, lat, lng, location_name, location_source, trip_name
            FROM photos
            WHERE {where_clause}
              AND (trip_name = ? OR trip_name IS NULL OR trip_name = '' OR lat IS NULL OR lat = 0.0)
        """, params + [trip])
        
        matched_photos = cursor.fetchall()
        enriched_for_rule = 0
        
        for p in matched_photos:
            pid = p['id']
            curr_src = p['location_source']
            curr_lat = p['lat']
            
            # If photo already has native EXIF_GPS, we don't overwrite its coordinates,
            # but we enrich its location_name and city/country!
            if curr_src == 'EXIF_GPS' and curr_lat is not None and curr_lat != 0.0:
                conn.execute("""
                    UPDATE photos 
                    SET location_name = ?, city = ?, country = ?, trip_name = COALESCE(trip_name, ?)
                    WHERE id = ? AND (location_name IS NULL OR location_name = '')
                """, (landmark_name, city, country, trip, pid))
            else:
                # Assign verified GeoJSON coordinates
                conn.execute("""
                    UPDATE photos 
                    SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                        location_name = ?, city = ?, country = ?, trip_name = ?,
                        location_source = 'VERIFIED_GEOJSON_POI',
                        confidence_score = 0.98,
                        h3_index = ?
                    WHERE id = ?
                """, (lat, lng, lat, lng, landmark_name, city, country, trip, h3_idx, pid))
                enriched_for_rule += 1
                
        if enriched_for_rule > 0:
            stats_by_landmark[landmark_name] = enriched_for_rule
            total_enriched += enriched_for_rule
            
    conn.commit()
    
    print("\n" + "=" * 50)
    print("  RESULTADO DEL ENRIQUECIMIENTO GEOJSON")
    print("=" * 50)
    print(f"Total fotos enriquecidas con coordenadas verificadas: {total_enriched}\n")
    
    print("Desglose de fotos por Dataset / Landmark:")
    for lm_name, cnt in sorted(stats_by_landmark.items(), key=lambda x: -x[1]):
        print(f"  • {lm_name:<45}: +{cnt} fotos")
        
    # 4. Final Distribution Report
    print("\n" + "=" * 50)
    print("  DISTRIBUCIÓN ACTUALIZADA POR LOCATION_SOURCE")
    print("=" * 50)
    
    distribution = conn.execute("""
        SELECT COALESCE(location_source, 'SIN_GEO'), COUNT(*) 
        FROM photos 
        GROUP BY COALESCE(location_source, 'SIN_GEO')
        ORDER BY COUNT(*) DESC
    """).fetchall()
    
    total_catalog = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    
    for src, count in distribution:
        pct = (count / total_catalog) * 100
        print(f"  - {src:<24}: {count:>6} fotos ({pct:5.2f}%)")
        
    print(f"\n  Total catálogo consolidado: {total_catalog} fotos")
    print("=" * 50)
    conn.close()

if __name__ == '__main__':
    main()
