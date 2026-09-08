import os
import sqlite3
import requests

DB_PATH = r"F:\photo_catalog.db"
SERVER_URL = "http://localhost:8000"

print("\n============================================================")
print("=== DIAGNÓSTICO DEL PIPELINE DE GEOLOCALIZACIÓN ===")
print("============================================================\n")

# 1. Verificar Base de Datos
if not os.path.exists(DB_PATH):
    print(f"❌ Error: No se encontró la base de datos en {DB_PATH}")
else:
    print(f"✓ Base de datos encontrada en {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Obtener tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t for t in cursor.fetchall()]
        print(f"✓ Tablas en la DB: {', '.join(tables)}")
        
        # Contar fotos
        if 'photos' in tables:
            cursor.execute("SELECT COUNT(*) FROM photos")
            total = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM photos WHERE latitude IS NULL OR longitude IS NULL")
            unmapped = cursor.fetchone()
            print(f"✓ Total fotos en DB: {total} (UNMAPPED: {unmapped})")
            
            # Ver rutas de Bosnia
            cursor.execute("SELECT file_path, filename FROM photos WHERE file_path LIKE '%Bosnia%' LIMIT 3")
            samples = cursor.fetchall()
            if samples:
                print("✓ Muestras de rutas de Bosnia registradas en tu DB:")
                for s in samples:
                    print(f"  - Ruta DB: {s}")
                    # Verificar existencia física
                    if os.path.exists(s):
                        print("    -> [✓ FÍSICAMENTE EXISTE EN EL DISCO]")
                    else:
                        print("    -> [❌ NO SE ENCUENTRA EN EL DISCO - ¡ESTA ES LA CAUSA DEL SINO!]")
            else:
                print("❌ No se encontraron fotos que mencionen 'Bosnia' en el campo file_path de la DB.")
        conn.close()
    except Exception as e:
        print(f"❌ Error leyendo la DB: {e}")

# 2. Verificar Servidor FastAPI
print("\n=== PROBANDO CONEXIÓN AL SERVIDOR (Puerto 8000) ===")
try:
    res = requests.get(f"{SERVER_URL}/api/health")
    print(f"✓ Servidor respondiendo: {res.status_code} - {res.json()}")
except Exception as e:
    print(f"❌ Error de conexión al servidor en {SERVER_URL}: {e}")
    print("Asegúrate de haber iniciado el servidor con: python -m uvicorn server:app --port 8000")

# 3. Probar Extracción de Visión con imagen dummy
print("\n=== PROBANDO ENVÍO DE IMAGEN A GEMINI (Inferencia Real) ===")
try:
    from PIL import Image
    import io
    img = Image.new('RGB', (10, 10), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    files = {'file': ('dummy.jpg', img_bytes, 'image/jpeg')}
    print("Enviando mini-imagen de prueba para verificar API Key y Endpoint...")
    res = requests.post(f"{SERVER_URL}/api/extract-voucher", files=files)
    print(f"✓ Código de respuesta: {res.status_code}")
    print(f"✓ Respuesta JSON: {res.json()}")
except Exception as e:
    print(f"❌ Error probando el endpoint de visión: {e}")

print("\n============================================================")
