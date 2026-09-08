import sys

sys.stdout.reconfigure(encoding='utf-8')

path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Reemplazar líneas 1341-1343 con el código correcto y seguro
target_snippet = """// [FIXED] buildTimeline filter protected
const filteredPhotos = (PHOTOS_DATA || []).filter(p => p && (p.filename || p.src || '').toString().toLowerCase().includes(''));"""

replacement_snippet = """counts[day.date] = (PHOTOS_DATA || []).filter(p => p && (p.datetime || p.date || "").startsWith(day.date)).length;"""

if target_snippet in text:
    text = text.replace(target_snippet, replacement_snippet)
    print("¡Snippet reemplazado con éxito!")
else:
    print("No se encontró el snippet exacto.")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("¡Archivos sincronizados!")
