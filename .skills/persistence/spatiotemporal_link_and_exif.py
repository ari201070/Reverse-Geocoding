"""
spatiotemporal_link_and_exif.py
================================
Paso 1: Cruza fotos (tabla photos) con lugares conocidos (tabla known_places)
        usando proximidad espacial + ventana de fecha del viaje.
Paso 2: Incrusta las coordenadas y etiquetas GPS/XPKeywords en los archivos JPEG.

Ejecutar: python spatiotemporal_link_and_exif.py
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    print("Instalando piexif...")
    os.system(f"{sys.executable} -m pip install piexif")
    import piexif
    PIEXIF_AVAILABLE = True

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

# --- Ventana temporal del viaje Roma/Vaticano ---
# Ajustar estas fechas al periodo real del viaje
TRIP_START = "2024-01-01"  # Fecha inicio (inclusive)
TRIP_END   = "2026-12-31"  # Fecha fin (inclusive, amplia para capturar todo)

# Radio de asignacion espacial: si una foto ya tiene GPS, buscar el known_place mas cercano
# Para fotos SIN GPS, se asigna el lugar del periodo de viaje con mayor frecuencia
PROXIMITY_DEG = 0.05  # ~5km en grados decimales


# ─────────────────────────────────────────────────────────────
# PASO 1: Cruce espaciotemporal
# ─────────────────────────────────────────────────────────────

def link_photos_to_places(conn):
    cursor = conn.cursor()

    # 1a. Fotos sin ubicacion que caen en el periodo del viaje
    cursor.execute('''
        SELECT id, file_path, date_taken, latitude, longitude
        FROM photos
        WHERE (latitude IS NULL OR longitude IS NULL OR (latitude = 0 AND longitude = 0))
          AND date_taken IS NOT NULL
          AND date_taken >= ?
          AND date_taken <= ?
    ''', (TRIP_START, TRIP_END + " 23:59:59"))

    blind_photos = cursor.fetchall()
    print(f"Fotos sin GPS en el periodo del viaje: {len(blind_photos)}")

    # 1b. Obtener todos los known_places con nombre no nulo
    cursor.execute('''
        SELECT id, name, anon_latitude, anon_longitude, place_data
        FROM known_places
        WHERE name IS NOT NULL AND name != 'Desconocido'
          AND anon_latitude IS NOT NULL
    ''')
    known = cursor.fetchall()
    print(f"Lugares conocidos disponibles: {len(known)}\n")

    if not known:
        print("AVISO: No hay lugares conocidos con nombre en la BD. Ejecutar import_recent_geojson.py primero.")
        return 0

    # Construir lookup de lugares por coordenada para asignacion rapida
    # Estrategia: asignar el lugar con mayor frecuencia en known_places
    # como "lugar dominante" del viaje, ya que la mayoria son Roma/Vaticano
    # Contar lugares por ciudad extraida del place_data
    place_counts = {}
    for kp in known:
        kp_id, kp_name, kp_lat, kp_lng, kp_data = kp
        try:
            data = json.loads(kp_data) if kp_data else {}
            props = data.get('properties', {})
            city = props.get('addr:city') or props.get('city') or ''
            country = props.get('addr:country') or props.get('country') or 'Italia'
        except Exception:
            city = ''
            country = 'Italia'

        key = (round(kp_lat, 2), round(kp_lng, 2))
        place_counts[key] = {
            'name': kp_name,
            'lat': kp_lat,
            'lng': kp_lng,
            'city': city,
            'country': country,
        }

    # Para fotos sin GPS: asignar el lugar con coordenadas mas representativas
    # Obtener el centroide de todos los lugares conocidos (sera Roma/area de viaje)
    all_lats = [kp[2] for kp in known if kp[2]]
    all_lngs = [kp[3] for kp in known if kp[3]]
    centroid_lat = round(sum(all_lats) / len(all_lats), 4) if all_lats else 41.9028
    centroid_lng = round(sum(all_lngs) / len(all_lngs), 4) if all_lngs else 12.4964

    # Lugar mas cercano al centroide como lugar representativo del viaje
    best_place = min(known, key=lambda kp: abs(kp[2] - centroid_lat) + abs(kp[3] - centroid_lng))
    default_name = best_place[1]
    default_lat  = best_place[2]
    default_lng  = best_place[3]

    try:
        data = json.loads(best_place[4]) if best_place[4] else {}
        props = data.get('properties', {})
        default_city    = props.get('addr:city') or 'Roma'
        default_country = props.get('addr:country') or 'Italia'
    except Exception:
        default_city    = 'Roma'
        default_country = 'Italia'

    print(f"Lugar representativo del viaje: {default_name} ({default_lat}, {default_lng})")
    print(f"Ciudad/Pais por defecto: {default_city}, {default_country}\n")

    # 1c. Actualizar fotos sin GPS con el lugar representativo del viaje
    linked = 0
    if blind_photos:
        cursor.executemany('''
            UPDATE photos
            SET latitude      = ?,
                longitude     = ?,
                location_name = ?,
                city          = ?,
                country       = ?,
                date_source   = 'SPATIOTEMPORAL_LINK'
            WHERE id = ?
        ''', [
            (default_lat, default_lng, default_name, default_city, default_country, photo[0])
            for photo in blind_photos
        ])
        linked = len(blind_photos)
        conn.commit()
        print(f"Fotos vinculadas al lugar representativo: {linked}")

    # 1d. Fotos que YA tienen GPS: buscar known_place mas cercano y enriquecer nombre/ciudad/pais
    cursor.execute('''
        SELECT id, file_path, latitude, longitude
        FROM photos
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND abs(latitude) > 0.001
          AND (location_name IS NULL OR location_name = '')
    ''')
    gps_photos = cursor.fetchall()
    print(f"\nFotos con GPS pero sin nombre de lugar: {len(gps_photos)}")

    enriched = 0
    for photo in gps_photos:
        pid, fpath, plat, plng = photo
        # Buscar el known_place mas cercano
        nearest = min(known, key=lambda kp: abs(kp[2] - plat) + abs(kp[3] - plng))
        dist = abs(nearest[2] - plat) + abs(nearest[3] - plng)
        if dist <= PROXIMITY_DEG:
            try:
                data = json.loads(nearest[4]) if nearest[4] else {}
                props = data.get('properties', {})
                n_city    = props.get('addr:city') or 'Roma'
                n_country = props.get('addr:country') or 'Italia'
            except Exception:
                n_city    = 'Roma'
                n_country = 'Italia'

            cursor.execute('''
                UPDATE photos
                SET location_name = ?,
                    city          = ?,
                    country       = ?,
                    date_source   = 'GPS_ENRICHED'
                WHERE id = ?
            ''', (nearest[1], n_city, n_country, pid))
            enriched += 1

    conn.commit()
    print(f"Fotos con GPS enriquecidas con nombre de lugar: {enriched}")
    return linked + enriched


# ─────────────────────────────────────────────────────────────
# PASO 2: Incrustacion EXIF
# ─────────────────────────────────────────────────────────────

def to_rational(value):
    """Convierte decimal a tupla de racionales EXIF (numerador, denominador)."""
    abs_val = abs(value)
    d = int(abs_val)
    m = int((abs_val - d) * 60)
    s = round((abs_val - d - m / 60.0) * 3600 * 10000)
    return ((d, 1), (m, 1), (s, 10000))

def embed_exif_to_file(file_path, lat, lng, poi_name, city, country):
    if not os.path.exists(file_path):
        return False, "no encontrado"
    if not file_path.lower().endswith(('.jpg', '.jpeg')):
        return False, "no es JPEG"
    try:
        exif_dict = piexif.load(file_path)

        # GPS
        lat_rational = to_rational(lat)
        lng_rational = to_rational(lng)
        lat_ref = b"S" if lat < 0 else b"N"
        lng_ref = b"W" if lng < 0 else b"E"

        gps_ifd = {
            piexif.GPSIFD.GPSLatitudeRef:  lat_ref,
            piexif.GPSIFD.GPSLatitude:     lat_rational,
            piexif.GPSIFD.GPSLongitudeRef: lng_ref,
            piexif.GPSIFD.GPSLongitude:    lng_rational,
        }

        # Keywords: "POI; Ciudad; Pais"
        parts = [p for p in [poi_name, city, country] if p]
        keywords = "; ".join(parts)
        kw_utf16 = keywords.encode('utf-16le')

        ifd0 = exif_dict.get("0th", {})
        ifd0[piexif.ImageIFD.XPKeywords]      = kw_utf16
        ifd0[piexif.ImageIFD.ImageDescription] = keywords.encode('utf-8')

        exif_dict["GPS"] = gps_ifd
        exif_dict["0th"] = ifd0

        # Preservar DateTimeOriginal — NO lo tocamos
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file_path)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def embed_all(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT file_path, latitude, longitude, location_name, city, country
        FROM photos
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND abs(latitude) > 0.001
    ''')
    photos = cursor.fetchall()

    if not photos:
        print("\nNo hay fotos con coordenadas para incrustar EXIF.")
        return

    print(f"\nFotos a procesar con EXIF: {len(photos)}")
    ok = 0
    skipped = 0
    errors = 0

    for i, (fpath, lat, lng, poi, city, country) in enumerate(photos, 1):
        success, msg = embed_exif_to_file(fpath, lat, lng, poi, city, country)
        if success:
            ok += 1
        elif msg == "no encontrado":
            skipped += 1
        else:
            errors += 1
            if errors <= 5:
                print(f"  Error [{msg}]: {fpath}")

        if i % 200 == 0:
            print(f"  ... {i}/{len(photos)} procesadas")

    print(f"\n=== REPORTE EXIF ===")
    print(f"Incrustadas exitosamente : {ok}")
    print(f"Saltadas (no encontradas): {skipped}")
    print(f"Errores de escritura     : {errors}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    conn.execute("PRAGMA journal_mode=WAL")

    # Verificar estado inicial
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM photos WHERE latitude IS NOT NULL AND abs(latitude) > 0.001")
    with_gps = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM photos")
    total_photos = cursor.fetchone()[0]

    print(f"=== ESTADO INICIAL ===")
    print(f"Fotos en la BD: {total_photos}")
    print(f"Fotos con GPS : {with_gps}\n")

    if total_photos == 0:
        print("AVISO: La tabla photos esta vacia. Ejecuta inject_photos.py primero para escanear F:\\ o G:\\.")
        print("Una vez cargada, este script realizara el cruce y la incrustacion EXIF automaticamente.")
        conn.close()
        return

    print("=== PASO 1: CRUCE ESPACIOTEMPORAL ===")
    total_linked = link_photos_to_places(conn)
    print(f"\nTotal de fotos vinculadas/enriquecidas: {total_linked}")

    print("\n=== PASO 2: INCRUSTACION EXIF ===")
    if PIEXIF_AVAILABLE:
        embed_all(conn)
    else:
        print("piexif no disponible, omitiendo incrustacion.")

    conn.close()
    print("\nProceso completado.")

if __name__ == '__main__':
    main()
