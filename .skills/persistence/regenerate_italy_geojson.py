#!/usr/bin/env python3
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""Regenera data/italy_2023_oct02_12.geojson desde data/photo_catalog.db (Italia)."""
import sqlite3, json, math
from datetime import datetime

try:
    import h3
except ImportError:
    h3 = None

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
OUT = 'data/italy_2023_oct02_12.geojson'

con = sqlite3.connect(DB, timeout=30)
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = con.cursor()

# Fase lectura: puntos (fotos Italia) con datos presentes
cur.execute("""
SELECT id, filename, date_taken, latitude, longitude, h3_index,
       place_name, location_source, tags
FROM photos WHERE country LIKE '%Italy%'
ORDER BY date_taken
""")
rows = cur.fetchall()

# Puntos GeoJSON
features = []
for r in rows:
    pid, fn, dt, lat, lng, h3_idx, place, src, tags = r
    # Redondeo a 4 decimales (privacidad y coherencia)
    lat_r = round(float(lat), 4) if lat is not None else None
    lng_r = round(float(lng), 4) if lng is not None else None
    if lat_r is not None and lng_r is not None:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lng_r, lat_r]
            },
            "properties": {
                "filename": fn,
                "date_taken": dt,
                "place": place or "",
                "source": src or "",
                "h3_index": h3_idx or ""
            }
        })

# Polígonos H3 res 9 (desde índices únicos presentes en el lote)
cur.execute("""
SELECT DISTINCT h3_index FROM photos WHERE country LIKE '%Italy%' AND h3_index IS NOT NULL
""")
h3_indices = [row[0] for row in cur.fetchall()]

if h3 is not None:
    for idx in h3_indices:
        # Contar fotos en esta celda H3
        cur.execute("SELECT COUNT(*) FROM photos WHERE country LIKE '%Italy%' AND h3_index = ?", (idx,))
        count = cur.fetchone()[0]
        boundary = h3.cell_to_boundary(idx)  # tupla de (lat, lng)
        # Convertir a [lng, lat] para GeoJSON y cerrar polígono
        polygon_coords = [[lng, lat] for lat, lng in boundary]
        # Cerrar polígono
        polygon_coords.append(polygon_coords[0])
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            },
            "properties": {
                "h3_index": idx,
                "kind": "h3_cell_res9",
                "photo_count": count
            }
        })

con.close()

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)

print(f"Regenerado {OUT}: {len([f for f in features if f['geometry']['type']=='Point'])} puntos, {len(h3_indices)} polígonos H3.")
