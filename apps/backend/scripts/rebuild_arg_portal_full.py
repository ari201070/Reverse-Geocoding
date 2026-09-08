import sqlite3, json, sys, os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, filename, latitude, longitude, location_name, location_address,
           city, date_taken, file_ext
    FROM photos
    WHERE trip_name = 'argentina-2025'
      AND latitude IS NOT NULL AND longitude IS NOT NULL
    ORDER BY date_taken
""")
db_rows = [dict(r) for r in cur.fetchall()]
conn.close()

trip_base = r'F:\2025\Octubre\Viaje Familiar de 30 dias por Argentina'
disk_folders = [d for d in os.listdir(trip_base) if os.path.isdir(os.path.join(trip_base, d)) and d != '_thumbs']

start_obj = datetime(2025, 9, 27)
photos_data = []
days_map = {}
cum_index = {}

for idx, p in enumerate(db_rows):
    dt = p['date_taken'] # formato "2025-09-27 10:06:35"
    date_str = dt[:10]
    filename = p['filename']
    
    # Calcular día del viaje
    try:
        d_obj = datetime.strptime(date_str, "%Y-%m-%d")
        d_day = max(1, (d_obj - start_obj).days + 1)
    except:
        d_day = 1

    # Encontrar ruta física en disco
    matching_folder = next((df for df in disk_folders if df.startswith(f"יום {d_day} ")), None)
    if matching_folder:
        src_path = f"Viaje Familiar de 30 dias por Argentina/{matching_folder}/{filename}"
    else:
        src_path = f"Viaje Familiar de 30 dias por Argentina/{filename}"

    loc_name = p['location_name'] or "Argentina"
    loc_addr = p['location_address'] or ""
    city = p['city'] or ""

    photo_obj = {
        "id": p['id'],
        "src": src_path,
        "filename": filename,
        "caption": loc_name,
        "dateTaken": date_str,
        "date": date_str,
        "datetime": dt,
        "lat": p['latitude'],
        "lng": p['longitude'],
        "lon": p['longitude'],
        "locationName": loc_name,
        "locationAddress": loc_addr,
        "city": city,
        "tripDay": d_day,
        "day": d_day,
        "cum": idx
    }
    photos_data.append(photo_obj)
    cum_index[filename] = idx

    if d_day not in days_map:
        days_map[d_day] = {
            "id": d_day,
            "date": date_str,
            "badge_es": f"DÍA {d_day}",
            "badge_he": f"יום {d_day}",
            "title_es": loc_name,
            "title_he": loc_name,
            "subtitle_es": loc_addr,
            "subtitle_he": loc_addr,
            "desc_es": f"Exploración en {loc_name}",
            "desc_he": f"פעילות ב-{loc_name}",
            "photos_count": 0,
            "center": [p['latitude'], p['longitude']]
        }
    days_map[d_day]["photos_count"] += 1
    # Actualizar el título del día con el primer lugar destacado
    if days_map[d_day]["title_es"] == "Argentina" and loc_name != "Argentina":
        days_map[d_day]["title_es"] = loc_name
        days_map[d_day]["title_he"] = loc_name

days_itinerary = [days_map[k] for k in sorted(days_map.keys())]

out_data = {
    "photos": photos_data,
    "days": days_itinerary,
    "cum_index": cum_index
}

data_json_path = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\data\argentina_data.json'
with open(data_json_path, 'w', encoding='utf-8') as f:
    json.dump(out_data, f, ensure_ascii=False, indent=2)

print(f"¡Generado argentina_data.json con {len(photos_data)} fotos y {len(days_itinerary)} días enriquecidos!")

# Inyectar en la plantilla maestra de Eslovenia
TEMPLATE = r"F:\2015\Julio\Viaje_Eslovenia_2015.html"
OUT_F = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
OUT_PUB = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    tmpl = f.read()

photos_start = tmpl.find("const PHOTOS_DATA = [")
photos_end = tmpl.find("];", photos_start) + 2

days_start = tmpl.find("const DAYS_ITINERARY = [")
days_end = tmpl.find("];", days_start) + 2

cum_start = tmpl.find("const PHOTO_CUM_INDEX = {")
cum_end = tmpl.find("};", cum_start) + 2

arg_photos = "const PHOTOS_DATA = " + json.dumps(photos_data, ensure_ascii=False) + ";"
arg_days = "const DAYS_ITINERARY = " + json.dumps(days_itinerary, ensure_ascii=False) + ";"
arg_cum = "const PHOTO_CUM_INDEX = " + json.dumps(cum_index, ensure_ascii=False) + ";"

result = tmpl[:photos_start] + arg_photos + "\n\n" + tmpl[photos_end:days_start] + arg_days + "\n\n" + tmpl[days_end:cum_start] + arg_cum + "\n\n" + tmpl[cum_end:]

result = result.replace("Eslovenia 2015", "Argentina 2025")
result = result.replace("Viaje_Eslovenia_2015", "Viaje_Argentina_2025")
result = result.replace("טיול בסלובניה 2015", "טיול בארגנטינה 2025")
result = result.replace('const PHOTO_BASE_PATH = "טיול בסלובניה";', 'const PHOTO_BASE_PATH = "Viaje Familiar de 30 dias por Argentina";')
result = result.replace('const PHOTO_BASE = "טיול בסלובניה/";', 'const PHOTO_BASE = "Viaje Familiar de 30 dias por Argentina/";')
result = result.replace("const mapCenter = [46.365, 14.05]", "const mapCenter = [-31.97, -63.45]")
result = result.replace("zoom: 12", "zoom: 5")

with open(OUT_F, 'w', encoding='utf-8') as f:
    f.write(result)
with open(OUT_PUB, 'w', encoding='utf-8') as f:
    f.write(result)

print("¡Portal de Argentina reconstruido con todos los detalles de ubicación, títulos y subtítulos de photo_catalog.db!")
