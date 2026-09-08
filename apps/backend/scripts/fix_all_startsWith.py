import sys, re

sys.stdout.reconfigure(encoding='utf-8')

# 1. Blindar TODOS los .startsWith en Argentina
arg_files = [
    r"F:\2025\Octubre\Viaje_Argentina_2025.html",
    r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"
]

for p in arg_files:
    with open(p, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Reemplazo de p.date.startsWith o p.datetime.startsWith
    text = text.replace(
        "const hasGPS = PHOTOS_DATA.some(p => p.date.startsWith(day.date) && p.lat !== null);",
        "const hasGPS = (PHOTOS_DATA || []).some(p => p && (p.datetime || p.date || '').toString().startsWith(day.date) && p.lat !== null);"
    )
    text = text.replace(
        "p.date.startsWith(day.date)",
        "(p.datetime || p.date || '').toString().startsWith(day.date)"
    )
    text = text.replace(
        "p.date.startsWith",
        "(p.datetime || p.date || '').toString().startsWith"
    )
    text = text.replace(
        "p.datetime.startsWith",
        "(p.datetime || p.date || '').toString().startsWith"
    )

    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)

# 2. Blindar TODOS los .startsWith en Eslovenia
slov_files = [
    r"F:\2015\Julio\Viaje_Eslovenia_2015.html",
    r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Eslovenia_2015.html"
]

for p in slov_files:
    with open(p, 'r', encoding='utf-8') as f:
        text = f.read()
    
    text = text.replace(
        "p.date.startsWith",
        "(p.datetime || p.date || '').toString().startsWith"
    )
    text = text.replace(
        "p.datetime.startsWith",
        "(p.datetime || p.date || '').toString().startsWith"
    )

    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)

print("¡Blindaje universal de startsWith completado en ambos portales!")
