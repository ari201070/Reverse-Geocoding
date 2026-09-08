import os, sys, json, re

sys.stdout.reconfigure(encoding='utf-8')

base_dir = r"F:\2025\Octubre"
enriched_path = os.path.join(base_dir, "Viaje_Argentina_2025_enriched.html")
basic_path = os.path.join(base_dir, "Viaje_Argentina_2025.html")
json_path = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025\src\imports\viajefamiliar30dias\public\data\photos.json"

print("1. Leyendo catálogo photos.json...")
with open(json_path, 'r', encoding='utf-8') as f:
    photos_data = json.load(f)

print(f"   Catálogo cargado: {len(photos_data)} fotos.")

print("2. Leyendo HTML enriquecido...")
with open(enriched_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Preparar la inyección de los datos del catálogo en el HTML
# Convertir photos_data a un string JSON seguro para incrustar en JavaScript
photos_json_str = json.dumps(photos_data, ensure_ascii=False)

# Reemplazar la estructura antigua de stagesData/photos por el nuevo catálogo local geolocalizado
# Buscamos dónde está definido stagesData o inyectamos nuestro script de carga local
injection_marker = "const stagesData = {"
if injection_marker in html_content:
    print("   Inyectando catálogo local en stagesData...")
    # Creamos un bloque que reemplace la carga por los datos locales de photos.json
    replacement = f"const localPhotosData = {photos_json_str};\nconst stagesData = {{"
    html_content = html_content.replace(injection_marker, replacement, 1)

# Modificar populatePhotos para que use localPhotosData
old_populate = "function populatePhotos() {"
new_populate = """function populatePhotos() {
            // Renderizado unificado desde photos.json local con GPS
            const scrollContainer = document.getElementById('scroll-argentina');
            if (scrollContainer && typeof localPhotosData !== 'undefined') {
                scrollContainer.innerHTML = '';
                localPhotosData.forEach(p => {
                    const item = document.createElement('div');
                    item.className = 'gallery-item';
                    item.innerHTML = `<img class="gallery-img" src="${p.src}" loading="lazy" />`;
                    item.addEventListener('click', (e) => {
                        e.stopPropagation();
                        openLightbox(p.src, p.caption || p.locationName, false);
                    });
                    scrollContainer.appendChild(item);
                });
            }"""

if old_populate in html_content:
    print("   Actualizando populatePhotos...")
    html_content = html_content.replace(old_populate, new_populate, 1)

print("3. Guardando Viaje_Argentina_2025.html unificado...")
with open(basic_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("4. Limpiando archivo _enriched.html sobrante...")
if os.path.exists(enriched_path):
    os.remove(enriched_path)
    print("   Viaje_Argentina_2025_enriched.html eliminado con éxito.")

print("¡Proceso de unificación profunda completado!")
PYEOF