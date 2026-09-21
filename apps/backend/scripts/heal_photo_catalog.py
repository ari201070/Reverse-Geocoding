import os
import sys
import io
import sqlite3
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

# Exact date ranges for all known trips
KNOWN_TRIPS = {
    'argentina-2011': {
        'start': '2011-11-07', 'end': '2012-02-06', 'country': 'Argentina'
    },
    'slovenia-2015': {
        'start': '2015-07-02', 'end': '2015-07-06', 'country': 'Slovenia'
    },
    'croatia-montenegro-2010': {
        'start': '2010-06-24', 'end': '2010-06-30', 'country': 'Croatia'
    },
    'crete-2013': {
        'start': '2013-07-23', 'end': '2013-07-27', 'country': 'Greece'
    },
    'italy-2023': {
        'start': '2023-10-03', 'end': '2023-10-11', 'country': 'Italy'
    },
    'bosnia-2023': {
        'start': '2023-05-01', 'end': '2023-05-05', 'country': 'Bosnia and Herzegovina'
    },
    'argentina-2025': {
        'start': '2025-09-26', 'end': '2025-10-30', 'country': 'Argentina'
    },
    'denmark-2024': {
        'start': '2024-09-15', 'end': '2024-09-20', 'country': 'Denmark'
    }
}

def parse_date_only(dt_str):
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    if len(dt_str) >= 10:
        date_part = dt_str[:10].replace(':', '-').replace('/', '-')
        if len(date_part) == 10 and date_part[0].isdigit() and date_part[4] == '-' and date_part[7] == '-':
            return date_part
    return None

def main():
    apply_changes = "--apply" in sys.argv
    mode = "[EJECUCIÓN REAL]" if apply_changes else "[MODO SIMULACIÓN - DRY RUN]"
    
    print("=" * 70)
    print(f"  {mode} SANEAMIENTO Y CURACIÓN TEMPORAL DEL CATÁLOGO")
    print(f"  Base de datos: {DB_PATH}")
    print("=" * 70)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # Fetch all photos
        cursor = conn.execute("""
            SELECT id, file_path, filename, date_taken, lat, lng, 
                   location_name, city, country, trip_name, location_source
            FROM photos
        """)
        photos = cursor.fetchall()
        
        total_photos = len(photos)
        print(f"Total fotos leídas de la base de datos: {total_photos}")
        
        incoherent_count = 0
        incoherent_details = []
        
        for p in photos:
            pid = p['id']
            file_path = p['file_path'] or ""
            filename = p['filename']
            date_taken = p['date_taken']
            trip_name = p['trip_name']
            lat = p['lat']
            lng = p['lng']
            country = p['country']
            city = p['city']
            loc_name = p['location_name']
            
            photo_date = parse_date_only(date_taken)
            if not photo_date:
                # If no date taken can be parsed, and it is assigned to a trip, we should flag it as suspicious!
                if trip_name:
                    incoherent_count += 1
                    incoherent_details.append({
                        'id': pid, 'file_path': file_path, 'filename': filename,
                        'date_taken': date_taken, 'photo_date': None,
                        'assigned_trip': trip_name, 'reason': 'Trip asignado sin fecha de captura'
                    })
                continue
                
            # If the photo has an assigned trip, verify if the photo date falls within that trip's range
            if trip_name:
                if trip_name in KNOWN_TRIPS:
                    trip = KNOWN_TRIPS[trip_name]
                    if not (trip['start'] <= photo_date <= trip['end']):
                        incoherent_count += 1
                        incoherent_details.append({
                            'id': pid, 'file_path': file_path, 'filename': filename,
                            'date_taken': date_taken, 'photo_date': photo_date,
                            'assigned_trip': trip_name,
                            'reason': f"Fecha de captura ({photo_date}) fuera de rango del viaje ({trip['start']} a {trip['end']})"
                        })
                else:
                    # Trip name is not in our known list of 8 trips
                    incoherent_count += 1
                    incoherent_details.append({
                        'id': pid, 'file_path': file_path, 'filename': filename,
                        'date_taken': date_taken, 'photo_date': photo_date,
                        'assigned_trip': trip_name, 'reason': f"Viaje desconocido '{trip_name}'"
                    })
                    
        print(f"\nSe detectaron {incoherent_count} registros con INCOHERENCIA TEMPORAL (Corrupción).")
        
        # Analyze distribution of corrupted rows
        by_trip_err = {}
        by_folder_err = {}
        for item in incoherent_details:
            trip = item['assigned_trip']
            by_trip_err[trip] = by_trip_err.get(trip, 0) + 1
            # Extract parent folder
            if item['file_path']:
                folder = os.path.dirname(item['file_path'])
                by_folder_err[folder] = by_folder_err.get(folder, 0) + 1
                
        print("\n--- Distribución de incoherencias por Viaje Asignado (Erróneo) ---")
        for trip, cnt in sorted(by_trip_err.items(), key=lambda x: -x[1]):
            print(f"  - {trip:<25}: {cnt} fotos")
            
        print("\n--- Carpetas físicas más contaminadas ---")
        for folder, cnt in sorted(by_folder_err.items(), key=lambda x: -x[1])[:15]:
            print(f"  - {folder}: {cnt} fotos")
            
        # Perform healings
        if apply_changes:
            print("\n" + "="*50)
            print("  APLICANDO CORRECCIONES EN LA BASE DE DATOS...")
            print("="*50)
            
            conn.execute("BEGIN TRANSACTION;")
            corrected_count = 0
            
            for item in incoherent_details:
                pid = item['id']
                p_date = item['photo_date']
                
                # Check if this photo's date actually fits another known trip!
                correct_trip = None
                correct_country = None
                if p_date:
                    for t_name, t_info in KNOWN_TRIPS.items():
                        if t_info['start'] <= p_date <= t_info['end']:
                            correct_trip = t_name
                            correct_country = t_info['country']
                            break
                            
                # Reset all fields and optionally assign the correct trip/country
                if correct_trip:
                    conn.execute("""
                        UPDATE photos 
                        SET trip_name = ?, country = ?, city = NULL, province = NULL,
                            latitude = NULL, longitude = NULL, lat = NULL, lng = NULL,
                            location_name = NULL, location_address = NULL, 
                            location_source = NULL, booking_id = NULL, confidence_score = NULL, h3_index = NULL
                        WHERE id = ?
                    """, (correct_trip, correct_country, pid))
                else:
                    conn.execute("""
                        UPDATE photos 
                        SET trip_name = NULL, country = NULL, city = NULL, province = NULL,
                            latitude = NULL, longitude = NULL, lat = NULL, lng = NULL,
                            location_name = NULL, location_address = NULL, 
                            location_source = NULL, booking_id = NULL, confidence_score = NULL, h3_index = NULL
                        WHERE id = ?
                    """, (pid,))
                    
                corrected_count += 1
                
            conn.commit()
            print(f"¡Saneamiento completado! Se han curado {corrected_count} registros corruptos en la base de datos.")
            
            # Print final clean state
            print("\n=== REPORTE DEL ESTADO SANO POST-CURACIÓN ===")
            rome_clean = conn.execute("""
                SELECT COUNT(*) FROM photos 
                WHERE lat BETWEEN 41.8 AND 42.0 AND lng BETWEEN 12.4 AND 12.6
            """).fetchone()[0]
            print(f"Total fotos en el recuadro de Roma: {rome_clean} (Originalmente: 609)")
            
            trip_clean_dist = conn.execute("""
                SELECT COALESCE(trip_name, 'SIN_VIAJE'), COUNT(*) 
                FROM photos 
                GROUP BY COALESCE(trip_name, 'SIN_VIAJE') 
                ORDER BY COUNT(*) DESC
            """).fetchall()
            print("\nNueva distribución de fotos por viaje:")
            for trip, cnt in trip_clean_dist:
                print(f"  - {trip:<25}: {cnt} fotos")
                
        else:
            print("\n[Aviso] No se realizaron cambios permanentes en la base de datos.")
            print("Para aplicar el saneamiento y curar el catálogo de fotos, ejecuta:")
            print("  python apps/backend/scripts/heal_photo_catalog.py --apply")
            
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Ocurrió un fallo en el proceso de saneamiento: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
