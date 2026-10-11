import os, sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
ROOT = 'F:/2023/05-Mayo'
con = sqlite3.connect('data/photo_catalog.db', timeout=30)
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM photos WHERE filename LIKE '%_Bosnia_2023%' AND trip_name='Bosnia 2023'")
print('bosnia_db:', cur.fetchone()[0], flush=True)
n_b = sum(1 for f in os.listdir(ROOT) if '_Bosnia_2023' in f)
n_i = sum(1 for f in os.listdir(ROOT) if '_Israel_2023' in f)
print(f'fisicos Bosnia: {n_b}, Israel: {n_i}', flush=True)
cur.execute("SELECT filename FROM photos WHERE filename='2023-05-01 08.41.30_Bosnia_2023.jpg'")
print('puntual:', cur.fetchone(), flush=True)
con.close()
