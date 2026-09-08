import json, sys, os

sys.stdout.reconfigure(encoding='utf-8')

data_path = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\data\argentina_data.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

trip_base = r'F:\2025\Octubre\Viaje Familiar de 30 dias por Argentina'

# Mapear carpetas reales de días por nombre o fecha
# Vamos a recorrer las carpetas físicas para asociar cada foto a su ruta relativa correcta
disk_folders = [d for d in os.listdir(trip_base) if os.path.isdir(os.path.join(trip_base, d)) and d != '_thumbs']

# Corregir cada src de foto usando el archivo real en disco
fixed = 0
for p in data['photos']:
    orig_fn = p['filename'] if 'filename' in p else os.path.basename(p['src'])
    # Buscar en qué carpeta de disco está este archivo
    found_rel = None
    for folder in disk_folders:
        folder_path = os.path.join(trip_base, folder)
        if os.path.exists(os.path.join(folder_path, orig_fn)):
            found_rel = f"Viaje Familiar de 30 dias por Argentina/{folder}/{orig_fn}"
            break
    
    if found_rel:
        p['src'] = found_rel
        fixed += 1
    else:
        # Fallback usando el día si no se encuentra exacto
        day_num = p.get('day', 1)
        # Buscar carpeta correspondiente al día
        matching_folder = next((df for df in disk_folders if df.startswith(f"יום {day_num} ")), None)
        if matching_folder:
            p['src'] = f"Viaje Familiar de 30 dias por Argentina/{matching_folder}/{orig_fn}"
            fixed += 1

with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"¡Corregidas {fixed} rutas de fotos en argentina_data.json!")

# Re-inyectar en Viaje_Argentina_2025.html
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

with open(OUT_F, 'w', encoding='utf-8') as f:
    f.write(result)
with open(OUT_PUB, 'w', encoding='utf-8') as f:
    f.write(result)

print("¡Portal de Argentina actualizado y sincronizado con las rutas reales de fotos!")
