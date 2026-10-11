import os
import sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

db_path = r"C:\Users\flier\.gemini\antigravity\scratch\Reverse-Geocoding\photo_catalog.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cursor = conn.cursor()

# Agregar columna filename si no existe
try:
    cursor.execute("ALTER TABLE photos ADD COLUMN filename TEXT")
    print("Columna 'filename' agregada OK.")
except Exception as e:
    print(f"(ya existe o error): {e}")

conn.commit()
conn.close()
print("Listo.")
