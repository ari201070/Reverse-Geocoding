import sys

sys.stdout.reconfigure(encoding='utf-8')

path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Corregir el acceso a filename en la línea 1409 para Argentina
old_line = "const isVideo = photo.filename.toLowerCase().endsWith('.mp4') || photo.filename.toLowerCase().endsWith('.mov');"
new_line = "const fn = photo.filename || photo.src || '';\nconst isVideo = fn.toLowerCase().endsWith('.mp4') || fn.toLowerCase().endsWith('.mov');"

text = text.replace(old_line, new_line)

# 2. Corregir thumbPath y relPath para que usen las carpetas de Argentina en lugar de 'טיול בסלובניה'
text = text.replace(
    'const thumbPath = dataIdx !== null ? `טיול בסלובניה/_thumbs/thumb_${dataIdx}.jpg` : null;',
    'const thumbPath = null; // No thumbs folder for Argentina yet, use src directly'
)
text = text.replace(
    'const relPath = photo.subfolder ? `טיול בסלובניה/${photo.subfolder}/${photo.filename}` : `טיול בסלובניה/${photo.filename}`;',
    'const relPath = photo.src;'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("¡Parche aplicado para corregir filename y rutas de Argentina en selectDay!")
