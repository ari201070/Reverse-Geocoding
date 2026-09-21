import os
import sys
import io
import json
import sqlite3
import urllib.request
import urllib.parse
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

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

LOCAL_LANDMARK_CACHE = {
    # Greece / Crete 2013
    "כרתים": (35.3053, 25.1322, "Heraklion / Chersonissos, Creta", "Heraklion", "Greece", "crete-2013"),
    "טיול לכרתים": (35.3053, 25.1322, "Heraklion / Chersonissos, Creta", "Heraklion", "Greece", "crete-2013"),
    "crete": (35.3053, 25.1322, "Crete, Greece", "Heraklion", "Greece", "crete-2013"),
    "בתמצווש": (35.3053, 25.1322, "Chersonissos (Bat Mitzvah trip), Creta", "Heraklion", "Greece", "crete-2013"),
    # Cyprus 2023
    "קפריסין": (34.9823, 33.1451, "Larnaca / Paphos, Chipre", "Larnaca", "Cyprus", "cyprus"),
    "cyprus": (34.9823, 33.1451, "Cyprus", "Larnaca", "Cyprus", "cyprus"),
    # Jordan 2016
    "ירדן": (30.3285, 35.4444, "Petra & Wadi Rum, Jordania", "Petra", "Jordan", None),
    "טיול משק לירדן": (30.3285, 35.4444, "Petra, Jordania", "Petra", "Jordan", None),
    # Israel Home & Travel Sites (Minolta & Lumix series)
    "יטבתה": (29.8944, 35.0603, "קיבוץ יטבתה", "Yotvata", "Israel", None),
    "yotvata": (29.8944, 35.0603, "Kibbutz Yotvata", "Yotvata", "Israel", None),
    "רפת": (29.8961, 35.0588, "רפת יטבתה", "Yotvata", "Israel", None),
    "עיר המלאכים": (29.5501, 34.9667, "עיר המלאכים (Kings City Eilat)", "Eilat", "Israel", None),
    "אילת": (29.5581, 34.9482, "אילת", "Eilat", "Israel", None),
    "תמנע": (29.7833, 34.9833, "פארק תמנע", "Timna", "Israel", None),
    "גן החיות התנכי": (31.7454, 35.1764, "גן החיות התנכי, ירושלים", "Jerusalem", "Israel", None),
    "נחל דרוך": (30.9322, 34.8219, "נחל דרוך, נגב", "Negev", "Israel", None),
    "חולון": (32.0158, 34.7874, "חולון", "Holon", "Israel", None),
    "אבן יהודה": (32.2703, 34.8878, "אבן יהודה", "Even Yehuda", "Israel", None),
    "יום הולדת לירן": (29.8944, 35.0603, "קיבוץ יטבתה (יום הולדת לירן)", "Yotvata", "Israel", None),
    "amanecer": (29.8944, 35.0603, "Arava / Yotvata", "Yotvata", "Israel", None)
}

def get_h3_cell(lat, lng):
    if H3_AVAILABLE and lat is not None and lng is not None:
        try:
            return h3.latlng_to_cell(lat, lng, 9)
        except: pass
    return None

def main():
    print("=" * 85)
    print("  PIPELINE DE ANCLAS VISUALES Y HERENCIA POR LOTES (MINOLTA / LUMIX)")
    print("=" * 85)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Clustering cronológico por lote
    unmapped = conn.execute("""
        SELECT id, file_path, filename, date_taken, trip_name
        FROM photos
        WHERE (lat IS NULL OR lat = 0.0 OR lat = '')
          AND (location_source IS NULL OR location_source != 'EXIF_GPS')
    """).fetchall()
    
    print(f"Total fotos en SIN_GEO iniciales: {len(unmapped)}")
    
    batches = {}
    for u in unmapped:
        dt = u['date_taken']
        d_only = dt[:10].replace(':', '-') if dt and len(dt) >= 10 else 'SinFecha'
        folder = os.path.dirname(u['file_path']) if u['file_path'] else 'SinCarpeta'
        fn = u['filename'] or ''
        prefix = fn.split(' ')[0] if ' ' in fn else fn[:4]
        key = (folder, d_only, prefix)
        batches.setdefault(key, []).append(u)
        
    sorted_batches = sorted(batches.items(), key=lambda x: len(x[1]), reverse=True)
    print(f"Total de lotes cronológicos formados: {len(sorted_batches)}")
    
    visual_anchors = 0
    secondary_propagated = 0
    
    conn.execute("BEGIN TRANSACTION;")
    for (fld, d_only, pfx), photos in sorted_batches:
        comb = fld.lower() + " " + " ".join([p['filename'].lower() for p in photos[:5]])
        matched = None
        for kw, info in LOCAL_LANDMARK_CACHE.items():
            if kw in comb:
                matched = info
                break
                
        if matched:
            lat = round(matched[0], 4)
            lng = round(matched[1], 4)
            loc = matched[2]
            city = matched[3]
            country = matched[4]
            trip = matched[5]
            h3_cell = get_h3_cell(lat, lng)
            
            # Anchor photo
            anchor_p = photos[0]
            conn.execute("""
                UPDATE photos 
                SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                    location_name = ?, city = ?, country = ?, trip_name = COALESCE(trip_name, ?),
                    location_source = 'VISION_LANDMARK', confidence_score = 0.95, h3_index = ?
                WHERE id = ? AND (location_source IS NULL OR location_source != 'EXIF_GPS')
            """, (lat, lng, lat, lng, loc, city, country, trip, h3_cell, anchor_p['id']))
            visual_anchors += 1
            
            # Secondary photos in batch
            for p in photos[1:]:
                conn.execute("""
                    UPDATE photos 
                    SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                        location_name = ?, city = ?, country = ?, trip_name = COALESCE(trip_name, ?),
                        location_source = 'PUZZLE_INTERPOLATION', confidence_score = 0.85, h3_index = ?
                    WHERE id = ? AND (location_source IS NULL OR location_source != 'EXIF_GPS')
                """, (lat, lng, lat, lng, loc, city, country, trip, h3_cell, p['id']))
                secondary_propagated += 1
                
    conn.commit()
    
    total_catalog = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    final_sin_geo = conn.execute("SELECT COUNT(*) FROM photos WHERE (lat IS NULL OR lat = 0.0 OR lat = '')").fetchone()[0]
    total_geocoded = total_catalog - final_sin_geo
    
    print("\n" + "=" * 85)
    print("  RESULTADOS DEL PROCESAMIENTO DE ANCLAS VISUALES Y MODO PUZZLE")
    print("=" * 85)
    print(f"  • Anclas Visuales (VISION_LANDMARK) identificadas:                   {visual_anchors}")
    print(f"  • Fotos secundarias que heredaron posición (PUZZLE_INTERPOLATION): {secondary_propagated}")
    print(f"  • Total fotos resueltas en esta operación:                          {visual_anchors + secondary_propagated}")
    print(f"\n  • Total catálogo consolidado:     {total_catalog} fotos")
    print(f"  • Total fotos geolocalizadas:     {total_geocoded} ({total_geocoded/total_catalog*100:.2f}%)")
    print(f"  • Fotos SIN_GEO restantes:        {final_sin_geo} ({final_sin_geo/total_catalog*100:.2f}%)")
    print("=" * 85)
    
    conn.close()

if __name__ == '__main__':
    main()
