import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

data_path = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\data\argentina_data.json'
if not os.path.exists(data_path):
    print("ERROR: No existe argentina_data.json")
    sys.exit(1)

with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total fotos en catálogo: {len(data['photos'])}")
sample_photo = data['photos'][2] # Día 2
print(f"Muestra Día 2 src: {sample_photo['src']}")

trip_base = r'F:\2025\Octubre'
full_path = os.path.join(trip_base, sample_photo['src'])
print(f"Ruta física completa: {full_path}")
print(f"¿Existe físicamente en disco?: {os.path.exists(full_path)}")
