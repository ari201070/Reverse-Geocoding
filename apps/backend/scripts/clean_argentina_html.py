import json, sys, os

sys.stdout.reconfigure(encoding='utf-8')

html_path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_html_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(html_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Corregir contadores estáticos de la cabecera (poner los valores reales de Argentina)
text = text.replace('<div class="stat-val" id="total-photos-val">670</div>', '<div class="stat-val" id="total-photos-val">2775</div>')
text = text.replace('<div class="stat-val" id="total-places-val">309</div>', '<div class="stat-val" id="total-places-val">32</div>')

# 2. Corregir dentro de selectDay la asignación de thumbPath y relPath:
# Reemplazar el bloque que hace referencia a טיול בסלובניה por el uso directo de photo.src
old_block = """const dataIdx = typeof photo.cum === 'number' ? photo.cum : (PHOTO_CUM_INDEX[photo.filename] ?? null);
                    const thumbPath = dataIdx !== null ? `טיול בסלובניה/_thumbs/thumb_${dataIdx}.jpg` : null;
                    const relPath = photo.subfolder ? `טיול בסלובניה/${photo.subfolder}/${photo.filename}` : `טיול בסלובניה/${photo.filename}`;
                    const isVideo = photo.filename.toLowerCase().endsWith('.mp4') || photo.filename.toLowerCase().endsWith('.mov');"""

new_block = """const fn = photo.filename || photo.src || '';
                    const isVideo = fn.toLowerCase().endsWith('.mp4') || fn.toLowerCase().endsWith('.mov');
                    const relPath = photo.src;
                    const thumbPath = null;"""

if old_block in text:
    text = text.replace(old_block, new_block)
    print("¡Bloque selectDay corregido con éxito!")
else:
    print("No se encontró el bloque exacto, aplicando reemplazos dirigidos...")
    text = text.replace("`טיול בסלובניה/_thumbs/thumb_${dataIdx}.jpg`", "null")
    text = text.replace("`טיול בסלובניה/${photo.subfolder}/${photo.filename}`", "photo.src")
    text = text.replace("`טיול בסלובניה/${photo.filename}`", "photo.src")
    text = text.replace("photo.filename.toLowerCase()", "(photo.filename || photo.src || '').toLowerCase()")

# 3. Corregir openLightbox para que use photo.src
old_lightbox = "const relPath = photo.subfolder ? `טיול בסלובניה/${photo.subfolder}/${photo.filename}` : `טיול בסלובניה/${photo.filename}`;"
new_lightbox = "const relPath = photo.src;"
text = text.replace(old_lightbox, new_lightbox)

# Guardar en ambos destinos
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(pub_html_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("¡Archivos HTML guardados y saneados completamente!")
