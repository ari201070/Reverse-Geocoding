import os
import sys
import io
import json
import sqlite3
import glob
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
BOOKINGS_DIR = r"C:\Users\flier\GitHub\Reverse-Geocoding\apps\backend\src\data"
BOOKINGS_PATH = os.path.join(BOOKINGS_DIR, "initialBookings.json")

# Master list of curated deterministic travel anchors & vouchers
MASTER_VOUCHERS = [
    # -------------------------------------------------------------
    # SLOVENIA 2015
    # -------------------------------------------------------------
    {
        "id": "voucher-auto-europe-slovenia-2015",
        "trip_name": "slovenia-2015",
        "category": "car_rental",
        "supplier": "Auto Europe / ATET Rent A Car",
        "title": "Alquiler VW Golf - Ljubljana Airport",
        "date_start": "2015-07-01",
        "start_time": "21:30",
        "date_end": "2015-07-08",
        "end_time": "21:30",
        "startDate": "2015-07-01",
        "endDate": "2015-07-08",
        "latitude": 46.2237,
        "longitude": 14.4576,
        "coordinates": {"lat": 46.2237, "lng": 14.4576},
        "location_name": "Aeropuerto de Liubliana Jože Pučnik (LJU), Eslovenia",
        "location": "Aeropuerto de Liubliana Jože Pučnik (LJU), Eslovenia"
    },
    {
        "id": "voucher-hotel-savica-bled-2015",
        "trip_name": "slovenia-2015",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "Hotel Savica - Sava Hotels & Resorts",
        "date_start": "2015-07-02",
        "start_time": "14:00",
        "date_end": "2015-07-05",
        "end_time": "11:00",
        "startDate": "2015-07-02",
        "endDate": "2015-07-05",
        "latitude": 46.3683,
        "longitude": 14.1122,
        "coordinates": {"lat": 46.3683, "lng": 14.1122},
        "location_name": "Hotel Savica, Bled, Eslovenia",
        "location": "Hotel Savica, Bled, Eslovenia"
    },
    {
        "id": "voucher-hotel-krim-bled-2015",
        "trip_name": "slovenia-2015",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "Hotel Krim Bled",
        "date_start": "2015-07-05",
        "start_time": "14:00",
        "date_end": "2015-07-06",
        "end_time": "11:00",
        "startDate": "2015-07-05",
        "endDate": "2015-07-06",
        "latitude": 46.3692,
        "longitude": 14.1147,
        "coordinates": {"lat": 46.3692, "lng": 14.1147},
        "location_name": "Hotel Krim, Bled, Eslovenia",
        "location": "Hotel Krim, Bled, Eslovenia"
    },
    {
        "id": "voucher-garni-hotel-azur-ljubljana-2015",
        "trip_name": "slovenia-2015",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "Garni Hotel Azur",
        "date_start": "2015-07-06",
        "start_time": "14:00",
        "date_end": "2015-07-07",
        "end_time": "11:00",
        "startDate": "2015-07-06",
        "endDate": "2015-07-07",
        "latitude": 46.0461,
        "longitude": 14.4794,
        "coordinates": {"lat": 46.0461, "lng": 14.4794},
        "location_name": "Garni Hotel Azur, Liubliana, Eslovenia",
        "location": "Garni Hotel Azur, Liubliana, Eslovenia"
    },

    # -------------------------------------------------------------
    # ARGENTINA 2025
    # -------------------------------------------------------------
    {
        "id": "voucher-vuelo-salta-iguazu-ar1795",
        "trip_name": "argentina-2025",
        "category": "flight",
        "supplier": "Aerolíneas Argentinas",
        "title": "Vuelo AR 1795: Salta (SLA) → Puerto Iguazú (IGR)",
        "date_start": "2025-10-19",
        "start_time": "13:15",
        "date_end": "2025-10-19",
        "end_time": "16:00",
        "startDate": "2025-10-19",
        "endDate": "2025-10-19",
        "latitude": -25.7372,
        "longitude": -54.4733,
        "coordinates": {"lat": -25.7372, "lng": -54.4733},
        "location_name": "Aeropuerto Internacional Cataratas del Iguazú (IGR), Misiones, Argentina",
        "location": "Aeropuerto Internacional Cataratas del Iguazú (IGR), Misiones, Argentina"
    },
    {
        "id": "voucher-andesmar-bariloche-mendoza-2025",
        "trip_name": "argentina-2025",
        "category": "bus",
        "supplier": "Andesmar / TRAMAT S.A.",
        "title": "Micro Larga Distancia: Bariloche → Mendoza (TX NTTZSH47)",
        "date_start": "2025-10-10",
        "start_time": "13:00",
        "date_end": "2025-10-11",
        "end_time": "07:00",
        "startDate": "2025-10-10",
        "endDate": "2025-10-11",
        "latitude": -32.8997,
        "longitude": -68.8322,
        "coordinates": {"lat": -32.8997, "lng": -68.8322},
        "location_name": "Terminal de Ómnibus de Mendoza, Argentina",
        "location": "Terminal de Ómnibus de Mendoza, Argentina"
    },
    {
        "id": "voucher-hotel-fuente-mayor-mendoza-2025",
        "trip_name": "argentina-2025",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "Fuente Mayor Hotel Centro Mendoza",
        "date_start": "2025-10-11",
        "start_time": "15:00",
        "date_end": "2025-10-14",
        "end_time": "11:00",
        "startDate": "2025-10-11",
        "endDate": "2025-10-14",
        "latitude": -32.88808,
        "longitude": -68.84638,
        "coordinates": {"lat": -32.88808, "lng": -68.84638},
        "location_name": "Fuente Mayor Hotel Centro, General Espejo 565, Mendoza, Argentina",
        "location": "Fuente Mayor Hotel Centro, General Espejo 565, Mendoza, Argentina"
    },
    {
        "id": "voucher-hotel-concorde-bariloche-2025",
        "trip_name": "argentina-2025",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "Hotel Concorde Bariloche",
        "date_start": "2025-10-05",
        "start_time": "14:00",
        "date_end": "2025-10-10",
        "end_time": "11:00",
        "startDate": "2025-10-05",
        "endDate": "2025-10-10",
        "latitude": -41.1334,
        "longitude": -71.3114,
        "coordinates": {"lat": -41.1334, "lng": -71.3114},
        "location_name": "Hotel Concorde, San Carlos de Bariloche, Río Negro, Argentina",
        "location": "Hotel Concorde, San Carlos de Bariloche, Río Negro, Argentina"
    },
    {
        "id": "voucher-buenos-aires-rosario-bus-2025",
        "trip_name": "argentina-2025",
        "category": "bus",
        "supplier": "Chevallier",
        "title": "Traslado Buenos Aires → Rosario",
        "date_start": "2025-09-30",
        "start_time": "08:00",
        "date_end": "2025-09-30",
        "end_time": "13:00",
        "startDate": "2025-09-30",
        "endDate": "2025-09-30",
        "latitude": -32.9442,
        "longitude": -60.6505,
        "coordinates": {"lat": -32.9442, "lng": -60.6505},
        "location_name": "Rosario, Santa Fe, Argentina",
        "location": "Rosario, Santa Fe, Argentina"
    },

    # -------------------------------------------------------------
    # ITALY 2023
    # -------------------------------------------------------------
    {
        "id": "voucher-sun-moon-rome-2023",
        "trip_name": "italy-2023",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "Hotel Sun & Moon Rome",
        "date_start": "2023-10-02",
        "start_time": "15:00",
        "date_end": "2023-10-05",
        "end_time": "10:00",
        "startDate": "2023-10-02",
        "endDate": "2023-10-05",
        "latitude": 41.9023,
        "longitude": 12.5054,
        "coordinates": {"lat": 41.9023, "lng": 12.5054},
        "location_name": "Hotel Sun & Moon, Roma, Italia",
        "location": "Hotel Sun & Moon, Roma, Italia"
    },
    {
        "id": "voucher-vatican-museums-tour-2023",
        "trip_name": "italy-2023",
        "category": "tour",
        "supplier": "Tripadvisor / Viator",
        "title": "Visita Guiada: Museos Vaticanos y Capilla Sixtina",
        "date_start": "2023-10-03",
        "start_time": "14:30",
        "date_end": "2023-10-03",
        "end_time": "18:30",
        "startDate": "2023-10-03",
        "endDate": "2023-10-03",
        "latitude": 41.9069,
        "longitude": 12.4533,
        "coordinates": {"lat": 41.9069, "lng": 12.4533},
        "location_name": "Capilla Sixtina y Museos Vaticanos, Ciudad del Vaticano",
        "location": "Capilla Sixtina y Museos Vaticanos, Ciudad del Vaticano"
    },
    {
        "id": "voucher-colosseum-tour-2023",
        "trip_name": "italy-2023",
        "category": "tour",
        "supplier": "Viator",
        "title": "Skip the Line: Colosseum, Roman Forum and Palatine Hill Tour",
        "date_start": "2023-10-04",
        "start_time": "14:30",
        "date_end": "2023-10-04",
        "end_time": "18:00",
        "startDate": "2023-10-04",
        "endDate": "2023-10-04",
        "latitude": 41.8906,
        "longitude": 12.4906,
        "coordinates": {"lat": 41.8906, "lng": 12.4906},
        "location_name": "Colosseo e Foro Romano, Roma, Italia",
        "location": "Colosseo e Foro Romano, Roma, Italia"
    },
    {
        "id": "voucher-pantheon-rome-2023",
        "trip_name": "italy-2023",
        "category": "tour",
        "supplier": "D'Uva Audioguide",
        "title": "Pantheon Reserved Entry & Audio Guide",
        "date_start": "2023-10-04",
        "start_time": "11:30",
        "date_end": "2023-10-04",
        "end_time": "13:00",
        "startDate": "2023-10-04",
        "endDate": "2023-10-04",
        "latitude": 41.8986,
        "longitude": 12.4769,
        "coordinates": {"lat": 41.8986, "lng": 12.4769},
        "location_name": "Pantheon, Piazza della Rotonda, Roma, Italia",
        "location": "Pantheon, Piazza della Rotonda, Roma, Italia"
    },
    {
        "id": "voucher-bb-marbo-florence-2023",
        "trip_name": "italy-2023",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "B&B Marbò Florence",
        "date_start": "2023-10-05",
        "start_time": "13:30",
        "date_end": "2023-10-09",
        "end_time": "11:00",
        "startDate": "2023-10-05",
        "endDate": "2023-10-09",
        "latitude": 43.7781,
        "longitude": 11.2454,
        "coordinates": {"lat": 43.7781, "lng": 11.2454},
        "location_name": "B&B Marbò Florence, Via Maragliano 100, Firenze, Italia",
        "location": "B&B Marbò Florence, Via Maragliano 100, Firenze, Italia"
    },
    {
        "id": "voucher-pisa-daytrip-2023",
        "trip_name": "italy-2023",
        "category": "day_trip",
        "supplier": "Trenitalia",
        "title": "Excursión Torre de Pisa",
        "date_start": "2023-10-06",
        "start_time": "09:30",
        "date_end": "2023-10-06",
        "end_time": "18:00",
        "startDate": "2023-10-06",
        "endDate": "2023-10-06",
        "latitude": 43.7228,
        "longitude": 10.3948,
        "coordinates": {"lat": 43.7228, "lng": 10.3948},
        "location_name": "Torre di Pisa, Piazza dei Miracoli, Pisa, Italia",
        "location": "Torre di Pisa, Piazza dei Miracoli, Pisa, Italia"
    },
    {
        "id": "voucher-hotel-soperga-milan-2023",
        "trip_name": "italy-2023",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "Hotel Soperga Milan",
        "date_start": "2023-10-09",
        "start_time": "14:00",
        "date_end": "2023-10-12",
        "end_time": "10:00",
        "startDate": "2023-10-09",
        "endDate": "2023-10-12",
        "latitude": 45.4885,
        "longitude": 9.2102,
        "coordinates": {"lat": 45.4885, "lng": 9.2102},
        "location_name": "Hotel Soperga, Via Beroldo 2, Milano, Italia",
        "location": "Hotel Soperga, Via Beroldo 2, Milano, Italia"
    },

    # -------------------------------------------------------------
    # DENMARK 2024
    # -------------------------------------------------------------
    {
        "id": "voucher-hotel-astoria-copenhagen-2024-1",
        "trip_name": "denmark-2024",
        "category": "hotel",
        "supplier": "Best Western",
        "title": "Hotel Astoria BW Signature Collection Copenhagen",
        "date_start": "2024-09-15",
        "start_time": "14:00",
        "date_end": "2024-09-16",
        "end_time": "11:00",
        "startDate": "2024-09-15",
        "endDate": "2024-09-16",
        "latitude": 55.6738,
        "longitude": 12.5645,
        "coordinates": {"lat": 55.6738, "lng": 12.5645},
        "location_name": "Hotel Astoria BW Signature Collection, Banegaardspladsen 4, Copenhagen, Denmark",
        "location": "Hotel Astoria BW Signature Collection, Banegaardspladsen 4, Copenhagen, Denmark"
    },
    {
        "id": "voucher-hotel-hillerod-denmark-2024",
        "trip_name": "denmark-2024",
        "category": "hotel",
        "supplier": "Best Western",
        "title": "Best Western Hotel Hillerod",
        "date_start": "2024-09-16",
        "start_time": "14:00",
        "date_end": "2024-09-20",
        "end_time": "11:00",
        "startDate": "2024-09-16",
        "endDate": "2024-09-20",
        "latitude": 55.9225,
        "longitude": 12.3042,
        "coordinates": {"lat": 55.9225, "lng": 12.3042},
        "location_name": "Best Western Hotel Hillerod, Milnersvej 41, Hillerod, Denmark",
        "location": "Best Western Hotel Hillerod, Milnersvej 41, Hillerod, Denmark"
    },
    {
        "id": "voucher-hotel-astoria-copenhagen-2024-2",
        "trip_name": "denmark-2024",
        "category": "hotel",
        "supplier": "Best Western",
        "title": "Hotel Astoria BW Signature Collection Copenhagen (Noche final)",
        "date_start": "2024-09-20",
        "start_time": "14:00",
        "date_end": "2024-09-21",
        "end_time": "11:00",
        "startDate": "2024-09-20",
        "endDate": "2024-09-21",
        "latitude": 55.6738,
        "longitude": 12.5645,
        "coordinates": {"lat": 55.6738, "lng": 12.5645},
        "location_name": "Hotel Astoria BW Signature Collection, Banegaardspladsen 4, Copenhagen, Denmark",
        "location": "Hotel Astoria BW Signature Collection, Banegaardspladsen 4, Copenhagen, Denmark"
    },

    # -------------------------------------------------------------
    # BOSNIA & HERZEGOVINA 2023
    # -------------------------------------------------------------
    {
        "id": "voucher-bih-sarajevo-base-2023",
        "trip_name": "bosnia-2023",
        "category": "hotel",
        "supplier": "Adama Travel",
        "title": "Estadía Sarajevo Base",
        "date_start": "2023-04-29",
        "start_time": "12:00",
        "date_end": "2023-04-30",
        "end_time": "23:59",
        "startDate": "2023-04-29",
        "endDate": "2023-04-30",
        "latitude": 43.8563,
        "longitude": 18.4131,
        "coordinates": {"lat": 43.8563, "lng": 18.4131},
        "location_name": "Sarajevo, Bosnia y Herzegovina",
        "location": "Sarajevo, Bosnia y Herzegovina"
    },
    {
        "id": "voucher-bih-mostar-base-2023",
        "trip_name": "bosnia-2023",
        "category": "hotel",
        "supplier": "Adama Travel",
        "title": "Estadía Mostar & Blagaj",
        "date_start": "2023-05-01",
        "start_time": "08:00",
        "date_end": "2023-05-02",
        "end_time": "23:59",
        "startDate": "2023-05-01",
        "endDate": "2023-05-02",
        "latitude": 43.3438,
        "longitude": 17.8078,
        "coordinates": {"lat": 43.3438, "lng": 17.8078},
        "location_name": "Stari Most, Mostar, Bosnia y Herzegovina",
        "location": "Stari Most, Mostar, Bosnia y Herzegovina"
    },
    {
        "id": "voucher-bih-jajce-base-2023",
        "trip_name": "bosnia-2023",
        "category": "hotel",
        "supplier": "Adama Travel",
        "title": "Estadía Jajce Cascadas",
        "date_start": "2023-05-03",
        "start_time": "08:00",
        "date_end": "2023-05-04",
        "end_time": "15:00",
        "startDate": "2023-05-03",
        "endDate": "2023-05-04",
        "latitude": 44.3419,
        "longitude": 17.2703,
        "coordinates": {"lat": 44.3419, "lng": 17.2703},
        "location_name": "Jajce Waterfalls, Jajce, Bosnia y Herzegovina",
        "location": "Jajce Waterfalls, Jajce, Bosnia y Herzegovina"
    },
    {
        "id": "voucher-bih-bihac-base-2023",
        "trip_name": "bosnia-2023",
        "category": "hotel",
        "supplier": "Adama Travel",
        "title": "Estadía Bihac Parque Nacional Una",
        "date_start": "2023-05-04",
        "start_time": "15:00",
        "date_end": "2023-05-06",
        "end_time": "12:00",
        "startDate": "2023-05-04",
        "endDate": "2023-05-06",
        "latitude": 44.8169,
        "longitude": 15.8708,
        "coordinates": {"lat": 44.8169, "lng": 15.8708},
        "location_name": "Bihać, Río Una, Bosnia y Herzegovina",
        "location": "Bihać, Río Una, Bosnia y Herzegovina"
    },

    # -------------------------------------------------------------
    # ARGENTINA 2011 - 2012
    # -------------------------------------------------------------
    {
        "id": "voucher-hotel-mundial-buenos-aires-2011",
        "trip_name": "argentina-2011",
        "category": "hotel",
        "supplier": "Booking.com",
        "title": "Hotel Mundial Buenos Aires",
        "date_start": "2011-11-07",
        "start_time": "14:00",
        "date_end": "2011-11-11",
        "end_time": "11:00",
        "startDate": "2011-11-07",
        "endDate": "2011-11-11",
        "latitude": -34.6083,
        "longitude": -58.3831,
        "coordinates": {"lat": -34.6083, "lng": -58.3831},
        "location_name": "Hotel Mundial, Av. de Mayo 1298, Buenos Aires, Argentina",
        "location": "Hotel Mundial, Av. de Mayo 1298, Buenos Aires, Argentina"
    }
]

def main():
    print("=" * 85)
    print("  COMPILACIÓN DE initialBookings.json Y MOTOR DE HERENCIA ESPACIO-TEMPORAL L1")
    print("=" * 85)
    
    # 1. Save curated bookings to initialBookings.json
    os.makedirs(BOOKINGS_DIR, exist_ok=True)
    with open(BOOKINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(MASTER_VOUCHERS, f, ensure_ascii=False, indent=2)
        
    print(f"Consolidado de vouchers guardado exitosamente en:\n  {BOOKINGS_PATH}")
    print(f"Total anclas deterministas registradas: {len(MASTER_VOUCHERS)}\n")
    
    # 2. Connect to database
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Fetch photos without GPS that have a valid date_taken
    cursor = conn.execute("""
        SELECT id, file_path, filename, date_taken 
        FROM photos 
        WHERE (lat IS NULL OR lat = 0.0 OR lat = '') 
          AND date_taken IS NOT NULL 
          AND date_taken != ''
    """)
    unmapped_photos = cursor.fetchall()
    print(f"Total fotos familiares sin geolocalizar (SIN_GEO) con fecha a procesar: {len(unmapped_photos)}")
    
    # Sort vouchers: specific tours/transport/hotels first (shortest duration first)
    def voucher_duration_minutes(v):
        try:
            st = datetime.strptime(f"{v['date_start']} {v.get('start_time', '00:00')}", "%Y-%m-%d %H:%M")
            et = datetime.strptime(f"{v['date_end']} {v.get('end_time', '23:59')}", "%Y-%m-%d %H:%M")
            return (et - st).total_seconds() / 60.0
        except:
            return 999999.0
            
    sorted_vouchers = sorted(MASTER_VOUCHERS, key=voucher_duration_minutes)
    
    inherited_count = 0
    by_trip = {}
    
    conn.execute("BEGIN TRANSACTION;")
    
    for p in unmapped_photos:
        pid = p['id']
        dt_str = p['date_taken']
        # Try parse photo datetime
        p_dt = None
        clean_dt = dt_str.replace(':', '-', 2) if ':' in dt_str[:10] else dt_str
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                p_dt = datetime.strptime(clean_dt[:19], fmt)
                break
            except:
                pass
                
        if not p_dt:
            continue
            
        p_date_str = p_dt.strftime("%Y-%m-%d")
        
        matched_voucher = None
        for v in sorted_vouchers:
            v_start = v['date_start']
            v_end = v['date_end']
            
            # Check date containment
            if v_start <= p_date_str <= v_end:
                # If specific time window is provided (e.g. tour / flight / bus), check time
                if v.get('start_time') and v.get('end_time') and v_start == v_end:
                    try:
                        v_st = datetime.strptime(f"{v_start} {v['start_time']}", "%Y-%m-%d %H:%M")
                        v_et = datetime.strptime(f"{v_end} {v['end_time']}", "%Y-%m-%d %H:%M")
                        if v_st <= p_dt <= v_et:
                            matched_voucher = v
                            break
                    except:
                        pass
                else:
                    matched_voucher = v
                    break
                    
        if matched_voucher:
            v_lat = matched_voucher['latitude']
            v_lng = matched_voucher['longitude']
            v_loc = matched_voucher['location_name']
            v_trip = matched_voucher['trip_name']
            v_id = matched_voucher['id']
            
            conn.execute("""
                UPDATE photos 
                SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                    location_name = ?, location_source = 'VOUCHER_INHERITANCE',
                    booking_id = ?, trip_name = ?, confidence_score = 0.95
                WHERE id = ?
            """, (v_lat, v_lng, v_lat, v_lng, v_loc, v_id, v_trip, pid))
            
            inherited_count += 1
            by_trip[v_trip] = by_trip.get(v_trip, 0) + 1
            
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("  RESULTADO DEL MOTOR DE HERENCIA L1 (VOUCHERS & DOCUMENTOS)")
    print("=" * 50)
    print(f"  • Total de fotos que heredaron coordenadas exactas: {inherited_count}")
    print("\nDesglose por Viaje:")
    for trip, cnt in sorted(by_trip.items(), key=lambda x: -x[1]):
        print(f"  - {trip:<25}: +{cnt} fotos geolocalizadas")
    print("=" * 50)

if __name__ == '__main__':
    main()
