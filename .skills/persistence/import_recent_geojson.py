import os
import json
import sqlite3
import glob
from datetime import datetime, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def main():
    downloads_dir = r"C:\Users\flier\Downloads"
    db_path = r"C:\Users\flier\.gemini\antigravity\scratch\Reverse-Geocoding\photo_catalog.db"
    
    # 1. Ubicacion y Filtro de Fecha
    two_weeks_ago = datetime.now() - timedelta(days=14)
    geojson_files = glob.glob(os.path.join(downloads_dir, "*.geojson"))
    
    recent_files = []
    for f in geojson_files:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(f))
            if mtime >= two_weeks_ago:
                recent_files.append(f)
        except Exception as e:
            print(f"No se pudo leer la fecha de {f}: {e}")
            
    print(f"Buscando en {downloads_dir}...")
    print(f"Archivos GeoJSON encontrados en las ultimas 2 semanas: {len(recent_files)}\n")
    
    # 3. Conexion a BD y creacion de tabla si no existe
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cursor = conn.cursor()
    
    # Adaptado de setup_db.sql para SQLite
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS known_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            place_id TEXT UNIQUE,
            anon_latitude REAL,
            anon_longitude REAL,
            place_data TEXT
        )
    ''')
    
    # 2 & 3. Lectura, Parsing e Ingesta
    total_features = 0
    inserted = 0
    updated = 0
    
    for file_path in recent_files:
        print(f"Procesando: {os.path.basename(file_path)}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            features = data.get('features', [])
            total_features += len(features)
            
            for feature in features:
                props = feature.get('properties', {})
                geom = feature.get('geometry', {})
                
                if geom is None or geom.get('type') != 'Point':
                    continue
                    
                coords = geom.get('coordinates', [0, 0])
                lng, lat = coords[0], coords[1]
                
                # Extraccion de atributos
                name = props.get('name') or props.get('title') or 'Desconocido'
                place_id = str(props.get('place_id') or props.get('@id') or f"{name}_{round(lat,4)}_{round(lng,4)}")
                
                place_data_json = json.dumps(feature)
                
                cursor.execute("SELECT id FROM known_places WHERE place_id = ?", (place_id,))
                exists = cursor.fetchone()
                
                cursor.execute('''
                    INSERT INTO known_places (name, place_id, anon_latitude, anon_longitude, place_data)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(place_id) DO UPDATE SET
                        name=excluded.name,
                        anon_latitude=excluded.anon_latitude,
                        anon_longitude=excluded.anon_longitude,
                        place_data=excluded.place_data
                ''', (name, place_id, round(lat, 4), round(lng, 4), place_data_json))
                
                if exists:
                    updated += 1
                else:
                    inserted += 1
                    
        except Exception as e:
            print(f" Error leyendo {os.path.basename(file_path)}: {e}")
            
    conn.commit()
    conn.close()
    
    # 4. Confirmacion
    print("\n=== REPORTE DE IMPORTACION ===")
    print(f"Archivos GeoJSON procesados: {len(recent_files)}")
    print(f"Puntos (Features) totales leidos: {total_features}")
    print(f"Registros nuevos insertados: {inserted}")
    print(f"Registros duplicados actualizados: {updated}")
    print("La base de datos 'photo_catalog.db' ha quedado sincronizada correctamente.")

if __name__ == '__main__':
    main()
