import json, sys

sys.stdout.reconfigure(encoding='utf-8')

data_path = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\data\argentina_data.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Reconstruir DAYS_ITINERARY agrupando estrictamente por el día real de la foto
days_dict = {}
for p in data['photos']:
    d = p.get('day', 1)
    date_str = p.get('date', '2025-09-27')
    loc_name = p.get('locationName', 'Argentina')
    
    if d not in days_dict:
        days_dict[d] = {
            "id": d,
            "date": date_str,
            "badge_es": f"DÍA {d}",
            "badge_he": f"יום {d}",
            "title_es": loc_name,
            "title_he": loc_name,
            "subtitle_es": p.get('locationAddress', ''),
            "subtitle_he": p.get('locationAddress', ''),
            "desc_es": f"Actividades en {loc_name}",
            "desc_he": f"פעילות ב-{loc_name}",
            "photos_count": 0,
            "center": [p.get('lat', -34.6), p.get('lng', -58.3)]
        }
    days_dict[d]['photos_count'] += 1
    # Mantener el primer lugar relevante como título del día
    if days_dict[d]['title_es'] in ['Argentina', ''] and loc_name not in ['Argentina', '']:
        days_dict[d]['title_es'] = loc_name
        days_dict[d]['title_he'] = loc_name

new_days = [days_dict[k] for k in sorted(days_dict.keys())]
data['days'] = new_days

with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"¡Itinerario reconstruido con {len(new_days)} días exactos agrupados por fecha y fotos!")

# Inyectar en el HTML de Argentina y public/travels
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

arg_photos = "const PHOTOS_DATA = " + json.dumps(data['photos'], ensure_ascii=False) + ";"
arg_days = "const DAYS_ITINERARY = " + json.dumps(data['days'], ensure_ascii=False) + ";"
arg_cum = "const PHOTO_CUM_INDEX = " + json.dumps(data['cum_index'], ensure_ascii=False) + ";"

result = tmpl[:photos_start] + arg_photos + "\n\n" + tmpl[photos_end:days_start] + arg_days + "\n\n" + tmpl[days_end:cum_start] + arg_cum + "\n\n" + tmpl[cum_end:]

result = result.replace("Eslovenia 2015", "Argentina 2025")
result = result.replace("Viaje_Eslovenia_2015", "Viaje_Argentina_2025")
result = result.replace("טיול בסלובניה 2015", "טיול בארגנטינה 2025")
result = result.replace('const PHOTO_BASE_PATH = "טיול בסלובניה";', 'const PHOTO_BASE_PATH = "Viaje Familiar de 30 dias por Argentina";')
result = result.replace('const PHOTO_BASE = "טיול בסלובניה/";', 'const PHOTO_BASE = "Viaje Familiar de 30 dias por Argentina/";')
result = result.replace("const mapCenter = [46.365, 14.05]", "const mapCenter = [-31.97, -63.45]")
result = result.replace("zoom: 12", "zoom: 5")

# Sincronizar el filtrado de selectDay para que use match estricto por day (tripDay) en lugar de p.date === day.date
old_select_filter = "const dayPhotos = PHOTOS_DATA.filter(p => p && p.date === day.date);"
new_select_filter = "const dayPhotos = PHOTOS_DATA.filter(p => p && (p.tripDay === day.id || p.day === day.id || p.date === day.date));"
result = result.replace(old_select_filter, new_select_filter)

for path_target in [OUT_F, OUT_PUB]:
    with open(path_target, 'w', encoding='utf-8') as f:
        f.write(result)

print("¡Portal de Argentina sincronizado con el Paso 3 (filtrado robusto por tripDay/date)! Espejo perfecto de Eslovenia.")
