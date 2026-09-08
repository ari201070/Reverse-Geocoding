import sqlite3
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
google_backup_dir = r"F:\copia de los datos de Google"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- ANÁLISIS DE RUTAS EN DB VS COPIA DE GOOGLE ---")

# Let's see how many photos in DB come from 'copia de los datos de Google' vs main folders
goog_count = conn.execute("SELECT COUNT(*) FROM photos WHERE original_path LIKE ? OR final_path LIKE ?", (f"%{google_backup_dir}%", f"%{google_backup_dir}%")).fetchone()[0]
total_count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]

print(f"Total fotos en DB: {total_count}")
print(f"Fotos en DB que apuntan a 'copia de los datos de Google': {goog_count}")

# Check what years are under copia de los datos de Google
subdirs = [d for d in os.listdir(google_backup_dir) if os.path.isdir(os.path.join(google_backup_dir, d))]
print(f"Subdirectorios en 'copia de los datos de Google': {subdirs}")

for sd in ["2019", "2023", "2024", "2025", "2026"]:
    sd_path = os.path.join(google_backup_dir, sd)
    if os.path.exists(sd_path):
        count_in_db = conn.execute("SELECT COUNT(*) FROM photos WHERE original_path LIKE ? OR final_path LIKE ?", (f"%{sd_path}%", f"%{sd_path}%")).fetchone()[0]
        print(f"  - {sd}: {count_in_db} archivos en DB apuntan directo a esta ruta.")

conn.close()
