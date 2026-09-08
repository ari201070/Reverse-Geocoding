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

photos = arg['photos']
days = arg['days']
cum = arg['cum_index']

# Extract header (before PHOTOS_DATA) and footer (after PHOTO_CUM_INDEX)
header_end = tmpl.find("const PHOTOS_DATA = [")
footer_start = tmpl.find("};", tmpl.find("const PHOTO_CUM_INDEX")) + 2

header = tmpl[:header_end]
footer = tmpl[footer_start:]

# Replace in header
header = header.replace("Eslovenia 2015", "Argentina 2025")
header = header.replace("Viaje_Eslovenia_2015", "Viaje_Argentina_2025")
header = header.replace("טיול בסלובניה 2015", "טיול בארגנטינה 2025")
header = header.replace('const PHOTO_BASE_PATH = "טיול בסלובניה";', 'const PHOTO_BASE_PATH = "Viaje Familiar de 30 dias por Argentina";')
header = header.replace('const PHOTO_BASE = "טיול בסלובניה/";', 'const PHOTO_BASE = "Viaje Familiar de 30 dias por Argentina/";')
header = header.replace("Central coordinates of Slovenia trip", "Central coordinates of Argentina trip")

# Replace in footer
footer = footer.replace("Eslovenia 2015", "Argentina 2025")
footer = footer.replace("Viaje_Eslovenia_2015", "Viaje_Argentina_2025")
footer = footer.replace("טיול בסלובניה", "טיול בארגנטינה")

# Map center for Argentina
footer = footer.replace("const mapCenter = [46.365, 14.05]", "const mapCenter = [-31.97, -63.45]")
footer = footer.replace("zoom: 12", "zoom: 5")

# Build data blocks
photos_block = "const PHOTOS_DATA = " + json.dumps(photos, ensure_ascii=False) + ";\n\n"
days_block = "const DAYS_ITINERARY = " + json.dumps(days, ensure_ascii=False) + ";\n\n"
cum_block = "const PHOTO_CUM_INDEX = " + json.dumps(cum, ensure_ascii=False) + ";\n\n"

full = header + photos_block + days_block + cum_block + footer

with open(OUT_F, 'w', encoding='utf-8') as f:
    f.write(full)
with open(OUT_PUB, 'w', encoding='utf-8') as f:
    f.write(full)

print(f"OK: {len(full)} chars, {len(photos)} photos, {len(days)} days")
