import sqlite3
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    import piexif
except ImportError:
    print("La libreria piexif no esta instalada. Instalando...")
    os.system(f"{sys.executable} -m pip install piexif")
    import piexif

def to_deg(value, loc):
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    
    abs_value = abs(value)
    d = int(abs_value)
    m = int((abs_value - d) * 60)
    s = round((abs_value - d - m/60.0) * 3600 * 100)
    
    return ((d, 1), (m, 1), (s, 100)), loc_value

def embed_exif(file_path, lat, lng, poi_name, city, country):
    if not os.path.exists(file_path):
        return False, "Archivo no encontrado"
        
    try:
        exif_dict = piexif.load(file_path)
        
        # 1. GPS Tags
        lat_deg, lat_ref = to_deg(lat, ["S", "N"])
        lng_deg, lng_ref = to_deg(lng, ["W", "E"])
        
        gps_ifd = {
            piexif.GPSIFD.GPSLatitudeRef: lat_ref.encode(),
            piexif.GPSIFD.GPSLatitude: lat_deg,
            piexif.GPSIFD.GPSLongitudeRef: lng_ref.encode(),
            piexif.GPSIFD.GPSLongitude: lng_deg
        }
        
        # 2. Keywords (XPKeywords for Windows)
        keywords_list = [k for k in [poi_name, city, country] if k]
        keywords = "; ".join(keywords_list)
        keywords_utf16 = keywords.encode('utf-16le')
        
        ifd0 = exif_dict.get("0th", {})
        ifd0[piexif.ImageIFD.XPKeywords] = keywords_utf16
        ifd0[piexif.ImageIFD.ImageDescription] = keywords.encode('utf-8')
        
        exif_dict["GPS"] = gps_ifd
        exif_dict["0th"] = ifd0
        
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file_path)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def main():
    db_path = r"C:\Users\flier\.gemini\antigravity\scratch\Reverse-Geocoding\photo_catalog.db"
    
    if not os.path.exists(db_path):
        print(f"Error: No se encontro la BD {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cursor = conn.cursor()
    
    # 1. Verificar si la tabla photos existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='photos'")
    if not cursor.fetchone():
        print("=== REPORTE DE INCRUSTACION EXIF ===")
        print("AVISO: La tabla 'photos' no existe en photo_catalog.db en este momento.")
        print("El script esta listo y validado estructuralmente, pero requiere que primero se ejecute la inyeccion de rutas de disco.")
        return
        
    # 2. Leer fotos
    cursor.execute('''
        SELECT file_path, latitude, longitude, location_name, city, country 
        FROM photos 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    ''')
    
    photos = cursor.fetchall()
    
    if not photos:
        print("No se encontraron fotos con ubicacion conocida en la base de datos.")
        return
        
    print(f"Se encontraron {len(photos)} fotos para actualizar EXIF.")
    
    success_count = 0
    error_count = 0
    
    for row in photos:
        file_path, lat, lng, poi_name, city, country = row
        ok, msg = embed_exif(file_path, lat, lng, poi_name, city, country)
        if ok:
            success_count += 1
        else:
            error_count += 1
            print(f"Error en {file_path}: {msg}")
            
    print("\n=== RESUMEN DE INCRUSTACION EXIF ===")
    print(f"Total procesadas: {len(photos)}")
    print(f"Actualizadas exitosamente: {success_count}")
    print(f"Errores: {error_count}")
    
    conn.close()

if __name__ == '__main__':
    main()
