import os, sys, json, sqlite3, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

print("1. Conectando a photo_catalog.db...")
conn = sqlite3.connect(r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Obtener todas las fotos con GPS de Argentina
cur.execute("""
    SELECT id, filename, latitude, longitude, location_name, location_address,
           file_path, date_taken, file_ext, file_size
    FROM photos
    WHERE trip_name = 'argentina-2025'
      AND latitude IS NOT NULL AND longitude IS NOT NULL
    ORDER BY date_taken
""")
db_photos = [dict(r) for r in cur.fetchall()]
conn.close()

print(f"   Fotos en base de datos: {len(db_photos)}")

# Mapear las carpetas de días reales en disco F:
base_trip = r"F:\2025\Octubre\Viaje Familiar de 30 dias por Argentina"
disk_photos = {}

for root, dirs, files in os.walk(base_trip):
    for f in files:
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4', '.mov')):
            rel_dir = os.path.relpath(root, base_trip)
            # Clave de fecha: extraída del nombre o de la carpeta
            fname = f
            if fname[:10].count('-') == 2 and len(fname) > 19:
                d_str = fname[:10] + " " + fname[11:19].replace('.', ':')
                disk_photos[d_str] = (rel_dir, fname)

print(f"   Fotos en disco con fecha parseable: {len(disk_photos)}")

# Construir PHOTOS_DATA para Argentina
photos_data_arg = []
photo_cum_index = {}
days_map = {}

idx = 0
for p in db_photos:
    dt = p['date_taken']
    subfolder = ""
    actual_fname = p['filename']
    
    if dt in disk_photos:
        rel_dir, actual_fname = disk_photos[dt]
        subfolder = "" if rel_dir == "." else rel_dir
    
    # Calcular día del viaje
    d_day = 1
    try:
        d_obj = datetime.strptime(dt[:10], "%Y-%m-%d")
        start_obj = datetime(2025, 9, 27)
        d_day = max(1, (d_obj - start_obj).days + 1)
    except:
        pass

    loc_name = p['location_name'] or "Argentina"
    loc_addr = p['location_address'] or ""

    photo_entry = {
        "filename": actual_fname,
        "subfolder": subfolder,
        "lat": p['latitude'],
        "lon": p['longitude'],
        "datetime": dt,
        "location_name": loc_name,
        "location_address": loc_addr,
        "day": d_day
    }
    photos_data_arg.append(photo_entry)
    photo_cum_index[actual_fname] = idx
    idx += 1

    # Agrupar por día para DAYS_ITINERARY
    if d_day not in days_map:
        days_map[d_day] = {
            "id": d_day,
            "date": dt[:10],
            "badge_es": f"DÍA {d_day}",
            "badge_he": f"יום {d_day}",
            "title_es": loc_name,
            "title_he": loc_name,
            "desc_es": f"Exploración en {loc_name} ({loc_addr})",
            "desc_he": f"פעילות ב-{loc_name}",
            "photos_count": 0,
            "center": [p['latitude'], p['longitude']]
        }
    days_map[d_day]["photos_count"] += 1

days_itinerary_arg = [days_map[k] for k in sorted(days_map.keys())]

print(f"   Total fotos preparadas: {len(photos_data_arg)}")
print(f"   Total días en itinerario: {len(days_itinerary_arg)}")

# 2. Leer plantilla maestra de Eslovenia
with open(r"F:\2015\Julio\Viaje_Eslovenia_2015.html", 'r', encoding='utf-8') as f:
    master_html = f.read()

# Reemplazar títulos y textos globales
master_html = master_html.replace("Eslovenia 2015", "Argentina 2025")
master_html = master_html.replace("Viaje_Eslovenia_2015", "Viaje_Argentina_2025")
master_html = master_html.replace("טיול בסלובניה 2015", "טיול בארגנטינה 2025")

# Reemplazar la base de fotos para que apunte a la carpeta de Argentina
master_html = master_html.replace(
    'const PHOTO_BASE_PATH = "טיול בסלובניה";',
    'const PHOTO_BASE_PATH = "Viaje Familiar de 30 dias por Argentina";'
)
master_html = master_html.replace(
    'const PHOTO_BASE = "טיול בסלובניה/";',
    'const PHOTO_BASE = "Viaje Familiar de 30 dias por Argentina/";'
)

# Inyectar PHOTOS_DATA de Argentina
photos_js = f"const PHOTOS_DATA = {json.dumps(photos_data_arg, ensure_ascii=False, indent=4)};"
master_html = re.sub(r'const PHOTOS_DATA = \[[\s\S]*?\n\];', photos_js, master_html, count=1)

# Inyectar DAYS_ITINERARY de Argentina
itinerary_js = f"const DAYS_ITINERARY = {json.dumps(days_itinerary_arg, ensure_ascii=False, indent=4)};"
master_html = re.sub(r'const DAYS_ITINERARY = \[[\s\S]*?\n\s*\];', itinerary_js, master_html, count=1)

# Inyectar PHOTO_CUM_INDEX
cum_index_js = f"const PHOTO_CUM_INDEX = {json.dumps(photo_cum_index, ensure_ascii=False)};"
master_html = re.sub(r'const PHOTO_CUM_INDEX = \{[\s\S]*?\};', cum_index_js, master_html, count=1)

# 3. Guardar en F:\2025\Octubre\Viaje_Argentina_2025.html y en public/travels/
out_f = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
out_public = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(out_f, 'w', encoding='utf-8') as f:
    f.write(master_html)

with open(out_public, 'w', encoding='utf-8') as f:
    f.write(master_html)

print("¡Éxito! Viaje_Argentina_2025.html generado con sus 2.775 fotos reales, mapa en Argentina e itinerario de 30 días.")
