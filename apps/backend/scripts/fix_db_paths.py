import sqlite3
import os

DB_PATH = r"F:\photo_catalog.db"

if not os.path.exists(DB_PATH):
    print(f"❌ No se encontró la DB en {DB_PATH}")
    exit()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Inspeccionar las columnas reales de la tabla 'photos'
cursor.execute("PRAGMA table_info(photos)")
columns = [col[1] for col in cursor.fetchall()]
print(f"✓ Columnas detectadas en tu tabla 'photos': {columns}")

# Determinar cuál es la columna de ruta de archivo activa
path_column = None
if "original_path" in columns:
    path_column = "original_path"
elif "file_path" in columns:
    path_column = "file_path"

if not path_column:
    print("❌ Error: No se encontró una columna de ruta compatible (original_path o file_path).")
    conn.close()
    exit()

print(f"🎯 Usando la columna '{path_column}' para actualizar las rutas.")

# 2. Verificar si existen registros de Bosnia
cursor.execute(f"SELECT {path_column} FROM photos WHERE {path_column} LIKE '%Bosnia%' LIMIT 1")
sample = cursor.fetchone()

if not sample:
    print("⚠️ No se encontraron registros que contengan 'Bosnia' en la base de datos.")
    conn.close()
    exit()

old_path_sample = sample
print(f"📍 Ruta actual registrada en la DB (muestra): {old_path_sample}")

# 3. Ejecutar la actualización masiva de rutas en SQLite
print("\n🔄 Actualizando rutas de 'G:\\האחסון שלי' a 'F:\\Fotos_Organizadas'...")
cursor.execute(f"""
    UPDATE photos 
    SET {path_column} = REPLACE(
        {path_column}, 
        'G:\\האחסון שלי\\טיול לבוסניה והרצגובינה', 
        'F:\\Fotos_Organizadas\\Viajes\\Bosnia_2023\\2023-05'
    )
    WHERE {path_column} LIKE 'G:\\%';
""")
rows_updated = cursor.rowcount
conn.commit()

print(f"✓ ¡Se actualizaron {rows_updated} rutas en la base de datos!")

# 4. Confirmación física final
cursor.execute(f"SELECT {path_column} FROM photos WHERE {path_column} LIKE '%Bosnia%' LIMIT 1")
new_sample = cursor.fetchone()
if new_sample:
    new_path = new_sample
    print(f"📍 Nueva ruta en la DB (muestra): {new_path}")
    if os.path.exists(new_path):
        print("🎉 [✓ FÍSICAMENTE ENCONTRADA EN EL DISCO] - ¡Las fotos ahora son 100% legibles!")
    else:
        print("❌ El archivo sigue sin encontrarse físicamente. Revisa si la ruta de tu disco F: coincide.")

conn.close()
