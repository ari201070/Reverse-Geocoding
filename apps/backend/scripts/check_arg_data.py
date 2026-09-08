import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\public\data\argentina_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

days_count = {}
for p in data['photos']:
    d = p.get('day')
    days_count[d] = days_count.get(d, 0) + 1

print("Conteo de fotos por dia:", sorted(days_count.items()))
print("Total dias en DAYS_ITINERARY:", len(data['days']))
print("Primeros 3 dias:", data['days'][:3])
