# -*- coding: utf-8 -*-
import os
import sys
import io
import sqlite3
import subprocess
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Forzar sys.path para resolución de módulos del monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
EXIFTOOL_PATH = r"C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe"
TARGET_FOLDER = r"F:\2023\10-Octubre"

# Filas protegidas por invariantes selladas (contrato de evidencias + tests Roma):
# trayecto Terravision (captura NULL) y cena Mercato (NULL). No repoblar.
EXCLUIDOS = {
    "2023-10-02 16.23.48_IMG_20231002_162348.jpg",
    "2023-10-02 16.23.58_IMG_20231002_162358.jpg",
    "2023-10-02 16.24.00_IMG_20231002_162400.jpg",
    "2023-10-02 16.30.50_IMG_20231002_163050.jpg",
    "2023-10-02 16.30.52_IMG_20231002_163052.jpg",
    "2023-10-02 18.50.12_IMG_20231002_185012.jpg",
    "2023-10-02 19.16.01.jpg",
    "2023-10-02 19.17.38.jpg",
}

# 1. Validar firma de la base de datos antes de operar
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cache';")
if not cursor.fetchone():
    print("❌ ALERTA CRÍTICA: Base de datos inválida. Abortando.")
    sys.exit(1)

print("🔒 [SSOT VALIDADA] Conectado a la base enriquecida del repositorio.")

# 2. Obtener los archivos JPG del disco físico
if not os.path.exists(TARGET_FOLDER):
    print(f"❌ La ruta {TARGET_FOLDER} no existe.")
    sys.exit(1)

files = [f for f in os.listdir(TARGET_FOLDER) if f.lower().endswith(('.jpg', '.jpeg'))]
print(f"🔎 Detectados {len(files)} archivos físicos para procesar.")

updated_count = 0
skipped_count = 0
conn.execute("BEGIN TRANSACTION;")

# Lote unico de ExifTool en JSON (un solo proceso, evita timeout por spawn masivo).
cmd = [EXIFTOOL_PATH, "-j", "-n", "-ext", "jpg", "-ext", "jpeg",
       "-GPSLatitude", "-GPSLongitude", "-ImageDescription", TARGET_FOLDER]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"Advertencia: ExifTool salio con codigo {result.returncode}; se procesa lo recuperado.")
    print((result.stderr or "")[:300])
lote = json.loads(result.stdout or "[]")
print(f"ExifTool devolvio {len(lote)} registros.")

for item in lote:
    file = os.path.basename(item.get("SourceFile", ""))
    if not file or file not in files:
        continue
    if file in EXCLUIDOS:
        skipped_count += 1
        continue
    gps_lat = item.get("GPSLatitude")
    gps_lng = item.get("GPSLongitude")
    desc = item.get("ImageDescription")
    if gps_lat is None or gps_lng is None or not desc:
        continue
    try:
        lat = round(float(gps_lat), 4)
        lng = round(float(gps_lng), 4)
    except (TypeError, ValueError):
        print(f"Advertencia: coordenadas no numericas en {file}")
        continue
    # LIKE con ESCAPE para no cruzar filas con _ como comodín.
    patron = "%" + file.replace("%", "/%").replace("_", "/_")
    cursor.execute("""
        UPDATE photos
        SET latitude = ?, longitude = ?, lat = ?, lng = ?, place_name = ?
        WHERE (file_path LIKE ? ESCAPE '/' OR filename = ?);
    """, (lat, lng, lat, lng, desc, patron, file))
    if cursor.rowcount > 0:
        updated_count += 1

conn.commit()
print(f"✨ [PROCESO COMPLETADO] Se actualizaron {updated_count} registros en la DB de C: basados en el EXIF de F:.")
print(f"🛡️ Omitidas {skipped_count} filas protegidas por invariante (trayecto + cena).")
conn.close()
