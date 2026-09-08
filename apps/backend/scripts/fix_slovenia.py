import sys

sys.stdout.reconfigure(encoding='utf-8')

for path in [r"F:\2015\Julio\Viaje_Eslovenia_2015.html", r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Eslovenia_2015.html"]:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    text = text.replace('p.filename.startsWith', '(p.filename || "").startsWith')
    text = text.replace('photo.filename.startsWith', '(photo.filename || "").startsWith')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

print("¡Corrección aplicada en Eslovenia!")
