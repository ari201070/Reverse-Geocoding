import json, sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Asegurar que en argentina_data.json las coordenadas tengan tanto 'lon' como 'lng'
data_path = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\data\argentina_data.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for p in data['photos']:
    if 'lng' in p and p['lng'] is not None and 'lon' not in p:
        p['lon'] = p['lng']
    elif 'lon' in p and p['lon'] is not None and 'lng' not in p:
        p['lng'] = p['lon']

with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print("¡Coordenadas sincronizadas (lat, lon, lng) en argentina_data.json!")

# 2. Corregir Viaje_Argentina_2025.html para que valide tanto lon como lng, y evitar favicon 404
html_path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_html_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Validación estricta en plotDayOnMap para Leaflet (evitar undefined)
old_plot = "if (p.lat !== null && p.lon !== null) {"
new_plot = "const validLon = p.lon !== undefined && p.lon !== null ? p.lon : p.lng;\n            if (p.lat !== null && p.lat !== undefined && validLon !== null && validLon !== undefined) {\n                const lngVal = validLon;"

html = html.replace(old_plot, new_plot)
html = html.replace("coords.push([p.lat, p.lon]);", "coords.push([p.lat, lngVal]);")
html = html.replace("L.marker([p.lat, p.lon],", "L.marker([p.lat, lngVal],")

# Añadir <link rel="icon" href="data:,"> en el <head> para silenciar el 404 de favicon.ico
html = html.replace("</head>", '<link rel="icon" href="data:,">\n</head>')

# Re-inyectar PHOTOS_DATA actualizado
photos_start = html.find("const PHOTOS_DATA = [")
photos_end = html.find("];", photos_start) + 2
arg_photos = "const PHOTOS_DATA = " + json.dumps(data['photos'], ensure_ascii=False) + ";"
html = html[:photos_start] + arg_photos + html[photos_end:]

for path_target in [html_path, pub_html_path]:
    with open(path_target, 'w', encoding='utf-8') as f:
        f.write(html)

print("¡Portal de Argentina optimizado y blindado contra coordenadas inválidas y favicon 404!")
