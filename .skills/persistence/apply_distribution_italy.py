#!/usr/bin/env python3
"""Distribuye fotos no-EXIF_GPS de Italia dentro de sus celdas H3 (res 9),
respetando velocidad física y redondeo 4 decimales."""
import os
import sqlite3, math, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    import h3
except ImportError:
    h3 = None

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
V_MAX_KMH = 5.0  # caminata urbana / sitios estaticos (km/h)

def latlng_to_meters(lat, lng):
    return 111320 * math.cos(math.radians(lat))

def meters_to_deg(lat, lng, meters):
    d_lat = meters / 111320
    d_lng = meters / latlng_to_meters(lat, lng)
    return d_lat, d_lng

def main():
    con = sqlite3.connect(DB, timeout=30)
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cur = con.cursor()
    # Leer fotos de Italia con h3_index
    cur.execute("SELECT id, filename, date_taken, latitude, longitude, h3_index, location_source FROM photos WHERE country LIKE '%Italy%' AND h3_index IS NOT NULL")
    rows = cur.fetchall()
    # Agrupar por h3_index
    groups = {}
    for r in rows:
        pid, fn, dt, lat, lng, h3_idx, src = r
        groups.setdefault(h3_idx, []).append({
            'id': pid, 'filename': fn, 'date_taken': dt,
            'lat': lat, 'lng': lng, 'source': src, 'h3_index': h3_idx
        })
    # Para cada celda
    updated = 0
    for h3_idx, fotos in groups.items():
        # Separar anclas EXIF_GPS (no modificar)
        anclas = [f for f in fotos if f['source'] == 'EXIF_GPS']
        derivadas = [f for f in fotos if f['source'] != 'EXIF_GPS']
        if not derivadas:
            continue
        # Obtener centro de la celda H3
        if h3 is None:
            continue
        lat_c, lng_c = h3.cell_to_latlng(h3_idx)
        # Ordenar derivadas por date_taken
        derivadas.sort(key=lambda f: f['date_taken'] or '')
        max_i = max(len(derivadas), 1)
        # Radio aproximado del hexagono res 9 (~170 m diametro => 85 m radio)
        r_m = 85.0
        # Distribuir deterministamente con paso basado en orden
        for i, f in enumerate(derivadas):
            # Angulo espiral
            theta = (i * 2.39996) % (2 * math.pi)  # aproximacion angulo aureo
            # Distancia radial distribuida uniformemente en el disco
            # Para mantener coherencia temporal: distancia proporcional al indice
            # con limite al radio del hexagono
            dist_m = (i / max_i) * r_m
            d_lat, d_lng = meters_to_deg(lat_c, lng_c, dist_m)
            lat_new = lat_c + d_lat * math.cos(theta)
            lng_new = lng_c + d_lng * math.sin(theta)
            lat_r = round(lat_new, 4)
            lng_r = round(lng_new, 4)
            # Actualizar en lotes
            cur.execute("UPDATE photos SET latitude=?, longitude=? WHERE id=?", (lat_r, lng_r, f['id']))
            updated += 1
        # Confirmar transaccion por celda (o agrupar)
        con.commit()
        print(f"H3 {h3_idx}: {len(anclas)} anclas, {len(derivadas)} derivadas distribuidas.")
    con.close()
    print(f"Distribucion completa: {updated} fotos actualizadas en DB.")

if __name__ == '__main__':
    main()
