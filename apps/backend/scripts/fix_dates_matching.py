import json, sys

sys.stdout.reconfigure(encoding='utf-8')

data_path = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\data\argentina_data.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for p in data['photos']:
    # Asegurar que tengan el campo date y datetime con formato YYYY-MM-DD
    dt = p.get('dateTaken') or p.get('datetime') or '2025-09-27'
    p['date'] = dt[:10]
    p['datetime'] = dt

with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print("¡Fechas unificadas (date/datetime) en todas las fotos de Argentina!")

# Re-inyectar en el template
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

# Actualizar el filtro en selectDay para que use p.date o p.datetime
result = result.replace(
    "const dayPhotos = PHOTOS_DATA.filter(p => (p.datetime || p.date || '').toString().startsWith(day.date));",
    "const dayPhotos = PHOTOS_DATA.filter(p => p && p.date === day.date);"
)

with open(OUT_F, 'w', encoding='utf-8') as f:
    f.write(result)
with open(OUT_PUB, 'w', encoding='utf-8') as f:
    f.write(result)

print("¡Portal de Argentina regenerado con coincidencia exacta por fecha (date)!")
