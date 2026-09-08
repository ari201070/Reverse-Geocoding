import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Corregir Eslovenia (rutas relativas para que el servidor local en :8000 encuentre las fotos y miniaturas)
slov_paths = [
    r"F:\2015\Julio\Viaje_Eslovenia_2015.html",
    r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Eslovenia_2015.html"
]

for p in slov_paths:
    with open(p, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Asegurar que el filtro en buildTimeline sea 100% seguro contra null/undefined
    text = text.replace(
        "counts[day.date] = PHOTOS_DATA.filter(p => p.date.startsWith(day.date)).length;",
        "counts[day.date] = (PHOTOS_DATA || []).filter(p => p && (p.datetime || p.date || '').toString().startsWith(day.date)).length;"
    )
    text = text.replace(
        "counts[day.date] = (PHOTOS_DATA || []).filter(p => p && p.date.startsWith(day.date)).length;",
        "counts[day.date] = (PHOTOS_DATA || []).filter(p => p && (p.datetime || p.date || '').toString().startsWith(day.date)).length;"
    )
    
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)

# 2. Corregir Argentina
arg_paths = [
    r"F:\2025\Octubre\Viaje_Argentina_2025.html",
    r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"
]

for p in arg_paths:
    with open(p, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Blindaje definitivo de buildTimeline
    text = text.replace(
        "counts[day.date] = (PHOTOS_DATA || []).filter(p => p && p.datetime && p.datetime.startsWith(day.date)).length;",
        "counts[day.date] = (PHOTOS_DATA || []).filter(p => p && (p.datetime || p.date || '').toString().startsWith(day.date)).length;"
    )
    text = text.replace(
        "counts[day.date] = PHOTOS_DATA.filter(p => p.date.startsWith(day.date)).length;",
        "counts[day.date] = (PHOTOS_DATA || []).filter(p => p && (p.datetime || p.date || '').toString().startsWith(day.date)).length;"
    )
    
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)

print("¡Ambos portales (Eslovenia y Argentina) corregidos y blindados!")
