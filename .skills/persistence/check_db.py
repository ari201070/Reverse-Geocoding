import os
import sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
db = sqlite3.connect('photo_catalog.db')
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cursor = db.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
for name, sql in cursor.fetchall():
    print(f"Table: {name}")
    print(sql)
    print("-" * 50)
