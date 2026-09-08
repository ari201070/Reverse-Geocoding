import sys

sys.stdout.reconfigure(encoding='utf-8')

path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
pub_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\travels\Viaje_Argentina_2025.html"

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_func = """function buildTimeline() {
            const container = document.getElementById('timeline-container');
            container.innerHTML = '';
            
            // Calculate photo count per day
            const counts = {};
            DAYS_ITINERARY.forEach(day => {
                // [FIXED] buildTimeline filter protected
                const filteredPhotos = (PHOTOS_DATA || []).filter(p => p && (p.filename || p.src || '').toString().toLowerCase().includes(''));
            });"""

new_func = """function buildTimeline() {
            const container = document.getElementById('timeline-container');
            container.innerHTML = '';
            
            // Calculate photo count per day
            const counts = {};
            DAYS_ITINERARY.forEach(day => {
                counts[day.date] = (PHOTOS_DATA || []).filter(p => p && (p.datetime || p.date || "").startsWith(day.date)).length;
            });"""

if old_func in text:
    text = text.replace(old_func, new_func)
    print("¡Función buildTimeline reemplazada con éxito!")
else:
    print("No se encontró el bloque exacto de buildTimeline.")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("¡Sincronizado!")
