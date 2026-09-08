import os, sys

sys.stdout.reconfigure(encoding='utf-8')

slovenia_path = r"F:\2015\Julio\Viaje_Eslovenia_2015.html"
argentina_path = r"F:\2025\Octubre\Viaje_Argentina_2025.html"

print("Leyendo plantilla base de Eslovenia...")
with open(slovenia_path, 'r', encoding='utf-8') as f:
    slov_content = f.read()

# Vamos a adaptar la plantilla de Eslovenia para que sea la plantilla maestra unificada.
# Cambiamos el título y adaptamos las referencias para el viaje a Argentina.
master_html = slov_content.replace(
    "<title>Eslovenia 2015 | Portal de Viaje de Ultra-Lujo</title>",
    "<title>Argentina 2025 | Portal de Viaje Familiar de 30 Días</title>"
).replace(
    "Eslovenia 2015",
    "Argentina 2025"
)

# Guardar como la nueva plantilla unificada maestra en F:\2025\Octubre\Viaje_Argentina_2025.html
print("Escribiendo el nuevo portal unificado de Argentina con el estándar maestro...")
with open(argentina_path, 'w', encoding='utf-8') as f:
    f.write(master_html)

print("¡Plantilla unificada con éxito! Ahora Argentina e Eslovenia comparten exactamente el mismo diseño, CSS, botones RTL y motor Leaflet.")
PYEOF
