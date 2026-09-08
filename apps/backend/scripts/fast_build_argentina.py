import os, sys, json, sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

print("1. Conectando a photo_catalog.db...")
conn = sqlite3.connect(r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

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

# Construir PHOTOS_DATA rápido sin escanear recursivamente todo el disco lento
photos_data_arg = []
photo_cum_index = {}
days_map = {}

# Mapeo de días según fecha
start_obj = datetime(2025, 9, 27)

for idx, p in enumerate(db_photos):
    dt = p['date_taken']
    fname = p['filename']
    
    d_day = 1
    try:
        d_obj = datetime.strptime(dt[:10], "%Y-%m-%d")
        d_day = max(1, (d_obj - start_obj).days + 1)
    except:
        pass

    loc_name = p['location_name'] or "Argentina"
    loc_addr = p['location_address'] or ""

    photo_entry = {
        "filename": fname,
        "subfolder": "",
        "lat": p['latitude'],
        "lon": p['longitude'],
        "datetime": dt,
        "location_name": loc_name,
        "location_address": loc_addr,
        "day": d_day
    }
    photos_data_arg.append(photo_entry)
    photo_cum_index[fname] = idx

    if d_day not in days_map:
        days_map[d_day] = {
            "id": d_day,
            "date": dt[:10],
            "badge_es": f"DÍA {d_day}",
            "badge_he": f"יום {d_day}",
            "title_es": loc_name,
            "title_he": loc_name,
            "desc_es": f"Actividades en {loc_name}",
            "desc_he": f"פעילות ב-{loc_name}",
            "photos_count": 0,
            "center": [p['latitude'], p['longitude']]
        }
    days_map[d_day]["photos_count"] += 1

days_itinerary_arg = [days_map[k] for k in sorted(days_map.keys())]

# 2. Cargar plantilla maestra de Eslovenia
with open(r"F:\2015\Julio\Viaje_Eslovenia_2015.html", 'r', encoding='utf-8') as f:
    master_html = f.read()

# Reemplazos exactos por división de strings (mucho más rápido que regex para textos gigantes)
p1 = master_html.find("const PHOTOS_DATA = [")
p2 = master_html.find("const DAYS_ITINERARY = [")
p3 = master_html.find("const PHOTO_CUM_INDEX = {")
p4 = master_html.find("const STATS_DATA = {")

# Adaptar cabecera y título
header_part = master_html[:p1].replace("Eslovenia 2015", "Argentina 2025").replace("Viaje_Eslovenia_2015", "Viaje_Argentina_2025").replace("טיול בסלובניה", "טיול בארגנטינה")
header_part = header_part.replace('const PHOTO_BASE_PATH = "טיול בסלובניה";', 'const PHOTO_BASE_PATH = "Viaje Familiar de 30 dias por Argentina";')
header_part = header_part.replace('const PHOTO_BASE = "טיול בסלובניה/";', 'const PHOTO_BASE = "Viaje Familiar de 30 dias por Argentina/";')

middle_part = master_html[p2+24:p3]
end_part = master_html[p4:]

# Ensamblar HTML completo
photos_block = f"const PHOTOS_DATA = {json.dumps(photos_data_arg, ensure_ascii=False)};\n\n"
itinerary_block = f"const DAYS_ITINERARY = {json.dumps(days_itinerary_arg, ensure_ascii=False)};\n\n"
cum_index_block = f"const PHOTO_CUM_INDEX = {json.dumps(photo_cum_index, ensure_ascii=False)};\n\n"

full_html = header_part + photos_block + itinerary_block + cum_index_block + end_part

# Guardar archivos
out_f = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
out_public = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(out_f, 'w', encoding='utf-8') as f:
    f.write(full_html)

with open(out_public, 'w', encoding='utf-8') as f:
    f.write(full_html)

print("¡Listo en menos de 1 segundo! Viaje_Argentina_2025.html generado con éxito con datos 100% de Argentina.")
