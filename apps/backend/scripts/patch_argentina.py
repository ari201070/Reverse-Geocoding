import sys

sys.stdout.reconfigure(encoding='utf-8')

path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Reemplazar cualquier .filename.startsWith por una versión segura en todo el archivo
text = text.replace('.filename.startsWith', '?.filename?.startsWith')
text = text.replace('p.filename', '(p && p.filename)')
text = text.replace('photo.filename', '(photo && photo.filename)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("¡Parche defensivo aplicado en Argentina!")
