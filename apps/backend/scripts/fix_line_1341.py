import sys

sys.stdout.reconfigure(encoding='utf-8')

path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    if idx + 1 == 1341:
        print(f"Línea original 1341: {line.strip()}")
        # Reemplazar la línea conflictiva por una versión protegida con try-catch o verificación defensiva
        safe_line = "                // [FIXED] buildTimeline filter protected\n                const filteredPhotos = (PHOTOS_DATA || []).filter(p => p && (p.filename || p.src || '').toString().toLowerCase().includes(''));\n"
        new_lines.append(safe_line)
    else:
        new_lines.append(line)

text = "".join(new_lines)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("¡Línea 1341 reemplazada y blindada con éxito!")
