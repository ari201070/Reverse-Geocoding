import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

TEMPLATE = r"F:\2015\Julio\Viaje_Eslovenia_2015.html"
DATA = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\data\argentina_data.json"
OUT_F = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
OUT_PUB = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    tmpl = f.read()

with open(DATA, 'r', encoding='utf-8') as f:
    arg = json.load(f)

# Find exact boundaries
photos_start = tmpl.find("const PHOTOS_DATA = [")
photos_end = tmpl.find("];", photos_start) + 2

days_start = tmpl.find("const DAYS_ITINERARY = [")
days_end = tmpl.find("];", days_start) + 2

cum_start = tmpl.find("const PHOTO_CUM_INDEX = {")
cum_end = tmpl.find("};", cum_start) + 2

# Replace data blocks with Argentina data
arg_photos = "const PHOTOS_DATA = " + json.dumps(arg['photos'], ensure_ascii=False) + ";"
arg_days = "const DAYS_ITINERARY = " + json.dumps(arg['days'], ensure_ascii=False) + ";"
arg_cum = "const PHOTO_CUM_INDEX = " + json.dumps(arg['cum_index'], ensure_ascii=False) + ";"

result = tmpl[:photos_start] + arg_photos + "\n\n" + tmpl[photos_end:days_start] + arg_days + "\n\n" + tmpl[days_end:cum_start] + arg_cum + "\n\n" + tmpl[cum_end:]

# Replace Slovenia -> Argentina
result = result.replace("Eslovenia 2015", "Argentina 2025")
result = result.replace("Viaje_Eslovenia_2015", "Viaje_Argentina_2025")
result = result.replace("טיול בסלובניה 2015", "טיול בארגנטינה 2025")
result = result.replace('const PHOTO_BASE_PATH = "טיול בסלובניה";', 'const PHOTO_BASE_PATH = "Viaje Familiar de 30 dias por Argentina";')
result = result.replace('const PHOTO_BASE = "טיול בסלובניה/";', 'const PHOTO_BASE = "Viaje Familiar de 30 dias por Argentina/";')
result = result.replace("const mapCenter = [46.365, 14.05]", "const mapCenter = [-31.97, -63.45]")
result = result.replace("zoom: 12", "zoom: 5")
result = result.replace("Central coordinates of Slovenia trip", "Central coordinates of Argentina trip")

with open(OUT_F, 'w', encoding='utf-8') as f:
    f.write(result)
with open(OUT_PUB, 'w', encoding='utf-8') as f:
    f.write(result)

print(f"OK: {len(result)} chars written")
