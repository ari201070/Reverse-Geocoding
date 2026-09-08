import sqlite3
import os

DB_PATH = r"F:\photo_catalog.db"

# Carpetas del disco F donde buscaremos si una foto no se encuentra en su ruta registrada
SEARCH_FOLDERS = [
    r"F:\Fotos_Organizadas\Viajes\Bosnia_2023\2023-05",
    r"F:\2023\05-Mayo",
    r"F:\2023\Mayo\Bosnia I Herzegobina",
    r"F:\2023\Mayo",
    r"F:\Documentos_Viaje\2023\Mayo"
]

if not os.path.exists(DB_PATH):
    print(f"❌ No se encontró la DB en {DB_PATH}")
    exit()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Determinar columna de ruta de archivo
cursor.execute("PRAGMA table_info(photos)")
cols = [col[1] for col in cursor.fetchall()]
path_column = "original_path" if "original_path" in cols else "file_path"
print(f"🎯 Usando columna '{path_column}' para el análisis.")

# 2. Obtener todas las fotos registradas
cursor.execute(f"SELECT id, {path_column}, filename FROM photos")
rows = cursor.fetchall()

total_checked = 0
already_ok = 0
repaired = 0
not_found = 0
updates = []

print("\n🔄 Verificando y reparando rutas físicas en el disco F...")
for row in rows:
    row_id, db_path, filename = row
    if not db_path:
        continue
    
    total_checked += 1
    
    # Si la ruta actual ya existe físicamente, está perfecta
    if os.path.exists(db_path):
        already_ok += 1
        continue
    
    # Si no existe, la buscamos en nuestros directorios candidatos
    found_locally = False
    for folder in SEARCH_FOLDERS:
        candidate_path = os.path.join(folder, filename)
        if os.path.exists(candidate_path):
            updates.append((candidate_path, row_id))
            repaired += 1
            found_locally = True
            break
            
    if not found_locally:
        not_found += 1

# 3. Aplicar las correcciones en la DB
if updates:
    print(f"\n⚙️ Aplicando {len(updates)} correcciones en la base de datos...")
    cursor.executemany(f"UPDATE photos SET {path_column} = ? WHERE id = ?", updates)
    conn.commit()

print("\n============================================================")
print("=== REPORTE DE REPARACIÓN DE RUTAS ===")
print("============================================================")
print(f"✓ Total fotos analizadas: {total_checked}")
print(f"✓ Rutas que ya estaban correctas: {already_ok}")
print(f"🎉 Rutas reparadas automáticamente: {repaired}")
print(f"❌ Fotos no encontradas en ningún directorio: {not_found}")
print("============================================================")

conn.close()
