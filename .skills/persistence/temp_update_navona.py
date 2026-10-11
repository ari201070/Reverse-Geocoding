import os
import sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

conn = sqlite3.connect('data/photo_catalog.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = conn.cursor()

updates = [
    # Bloque Piazza Navona (verificado visualmente: Sant'Agnese + obelisco + fuente)
    (['2023-10-04 10.36.26_IMG_20231004_103626.jpg',
      '2023-10-04 10.36.29_IMG_20231004_103629.jpg',
      '2023-10-04 10.38.15_IMG_20231004_103815.jpg',
      '2023-10-04 10.38.17_IMG_20231004_103817.jpg',
      '2023-10-04 10.38.20_IMG_20231004_103820.jpg',
      '2023-10-04 10.38.20_IMG_20231004_103820_1.jpg'],
     41.8990, 12.4729, 'Piazza Navona, Roma, Italia'),
    # Panteon (foto verificada visualmente por el usuario)
    (['2023-10-04 11.33.03_IMG_20231004_113303.jpg'],
     41.8986, 12.4768, 'Pantheon de Roma, Piazza della Rotonda, Roma, Italia'),
    # Coliseo (foto verificada visualmente por el usuario, rafaga 4s)
    (['2023-10-04 13.32.56_IMG_20231004_133256.jpg',
      '2023-10-04 13.33.00_IMG_20231004_133300.jpg'],
     41.8905, 12.4925, 'Colosseo, Piazza del Colosseo, Roma, Italia'),
]

total = 0
for filenames, lat, lon, name in updates:
    for fn in filenames:
        cur.execute(
            'UPDATE photos SET latitude=?, longitude=?, lat=?, lng=?, '
            "location_name=?, location_source='VISUAL_LANDMARK_STRICT' "
            'WHERE filename=?',
            (lat, lon, lat, lon, name, fn))
        total += cur.rowcount
        print('OK' if cur.rowcount else 'MISS', fn)

conn.commit()
print('TOTAL_ACTUALIZADOS:', total)
conn.close()
