import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

def main():
    print("=== AGREGANDO COLUMNAS Y SINCRONIZANDO SCHEMA DE BASE DE DATOS ===")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("PRAGMA table_info(photos)")
        columns = [row[1] for row in cursor.fetchall()]
        print("Columnas actuales:", columns)
        
        # Add missing columns
        added = False
        conn.execute("BEGIN TRANSACTION;")
        
        if 'location_source' not in columns:
            print("Agregando columna 'location_source'...")
            conn.execute("ALTER TABLE photos ADD COLUMN location_source TEXT")
            added = True
            
        if 'booking_id' not in columns:
            print("Agregando columna 'booking_id'...")
            conn.execute("ALTER TABLE photos ADD COLUMN booking_id TEXT")
            added = True
            
        if 'lat' not in columns:
            print("Agregando columna 'lat'...")
            conn.execute("ALTER TABLE photos ADD COLUMN lat REAL")
            added = True
            
        if 'lng' not in columns:
            print("Agregando columna 'lng'...")
            conn.execute("ALTER TABLE photos ADD COLUMN lng REAL")
            added = True
            
        if 'confidence_score' not in columns:
            print("Agregando columna 'confidence_score'...")
            conn.execute("ALTER TABLE photos ADD COLUMN confidence_score REAL")
            added = True
            
        if 'h3_index' not in columns:
            print("Agregando columna 'h3_index'...")
            conn.execute("ALTER TABLE photos ADD COLUMN h3_index TEXT")
            added = True
            
        if 'province' not in columns:
            print("Agregando columna 'province'...")
            conn.execute("ALTER TABLE photos ADD COLUMN province TEXT")
            added = True
            
        conn.commit()
        print("¡Estructura de la base de datos actualizada con éxito!")
        
        # Synchronize coordinates
        print("\nSincronizando coordenadas: copiando 'latitude' -> 'lat' y 'longitude' -> 'lng'...")
        conn.execute("BEGIN TRANSACTION;")
        
        # We only copy if lat/lng are NULL but latitude/longitude are NOT NULL
        conn.execute("""
            UPDATE photos 
            SET lat = latitude, lng = longitude 
            WHERE lat IS NULL AND latitude IS NOT NULL
        """)
        
        # Also copy backwards just in case
        conn.execute("""
            UPDATE photos 
            SET latitude = lat, longitude = lng 
            WHERE latitude IS NULL AND lat IS NOT NULL
        """)
        
        # For photos that already have valid GPS EXIF coordinates, let's mark their location_source as 'EXIF_GPS'
        # if it is currently NULL.
        conn.execute("""
            UPDATE photos
            SET location_source = 'EXIF_GPS'
            WHERE location_source IS NULL 
              AND lat IS NOT NULL 
              AND lng IS NOT NULL 
              AND lat != 0.0 
              AND lng != 0.0
        """)
        
        conn.commit()
        print("¡Sincronización de coordenadas y metadatos completada!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error durante la actualización: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
