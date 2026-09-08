import sys

sys.stdout.reconfigure(encoding='utf-8')

path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Reemplazar el bloque defectuoso con el conteo real y seguro basado en day o date
old_block = """const counts = {};
DAYS_ITINERARY.forEach(day => {
// [FIXED] buildTimeline filter protected
const filteredPhotos = (PHOTOS_DATA || []).filter(p => p && (p.filename || p.src || '').toString().toLowerCase().includes(''));
});"""

new_block = """const counts = {};
DAYS_ITINERARY.forEach(day => {
    counts[day.date] = (PHOTOS_DATA || []).filter(p => p && p.datetime && p.datetime.startsWith(day.date)).length;
});"""

if old_block in text:
    text = text.replace(old_block, new_block)
    print("Bloque reemplazado correctamente con .datetime.startsWith")
else:
    print("No se encontró el bloque exacto, aplicando reemplazo alternativo...")
    text = text.replace(
        'counts[day.date] = PHOTOS_DATA.filter(p => p.date.startsWith(day.date)).length;',
        'counts[day.date] = (PHOTOS_DATA || []).filter(p => p && (p.datetime || p.date || "").startsWith(day.date)).length;'
    )

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("¡Parche definitivo aplicado en Argentina!")
