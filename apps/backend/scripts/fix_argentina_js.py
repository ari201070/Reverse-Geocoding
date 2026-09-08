import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(html_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Corregir el error de 'startsWith' protegiendo el acceso a propiedades en buildTimeline o populatePhotos
# Buscamos la línea que causa el error y la envolvemos con opcional o validación
old_code = 'p.filename.startsWith'
new_code = '(p.filename || "").startsWith'

if old_code in text:
    text = text.replace(old_code, new_code)
    print("Protegido con éxito el acceso a startsWith.")

# Asegurar que PHOTO_BASE_PATH apunte a la carpeta correcta de Argentina con _thumbs
old_base = 'const PHOTO_BASE_PATH = "Viaje Familiar de 30 dias por Argentina";'
new_base = 'const PHOTO_BASE_PATH = "Viaje Familiar de 30 dias por Argentina";\nconst THUMBS_FOLDER = "_thumbs";'
if old_base in text and "_thumbs" not in text:
    text = text.replace(old_base, new_base)
    print("Añadida la referencia a _thumbs.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("¡Correcciones aplicadas en Viaje_Argentina_2025.html!")
PYEOF