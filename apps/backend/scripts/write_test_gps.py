import os
import subprocess
import shutil

EXIFTOOL_PATH = r"C:\Users\flier\AppData\Local\Programs\ExifTool\exiftool.EXE"
if not os.path.exists(EXIFTOOL_PATH):
    EXIFTOOL_PATH = "exiftool"

TEST_SRC = r"F:\1983\11-Noviembre\2010-11-14 18.51.13_Scan_Pic0029_gfpgan.jpg"
TEST_DST = r"F:\1983\06-Junio\Precision_Rostros\test_gps_exiftool.jpg"

if not os.path.exists("F:\\"):
    TEST_SRC = os.path.join("1983", "11-Noviembre", "2010-11-14 18.51.13_Scan_Pic0029_gfpgan.jpg")
    TEST_DST = os.path.join("1983", "06-Junio", "Precision_Rostros", "test_gps_exiftool.jpg")

def main():
    if not os.path.exists(TEST_SRC):
        print(f"Error: No se encuentra la foto de prueba original en: {TEST_SRC}")
        return

    os.makedirs(os.path.dirname(TEST_DST), exist_ok=True)
    shutil.copy(TEST_SRC, TEST_DST)
    print(f"[OK] Copia de prueba creada en: {TEST_DST}")

    lat = -41.133433
    lng = -71.311417

    cmd = [
        EXIFTOOL_PATH,
        f"-GPSLatitude={lat}",
        f"-GPSLongitude={lng}",
        "-GPSLatitudeRef=S",
        "-GPSLongitudeRef=W",
        "-overwrite_original",
        TEST_DST
    ]

    print("Inyectando coordenadas GPS con ExifTool...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("\n==================================================")
        print("TEST DE EXIFTOOL EXITOSO:")
        print(f" - Coordenadas inyectadas: S {abs(lat)}, W {abs(lng)}")
        print(f" - Archivo modificado: {TEST_DST}")
        print("==================================================")
        
        verify_cmd = [EXIFTOOL_PATH, "-GPSLatitude", "-GPSLongitude", TEST_DST]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        print("Verificación de lectura EXIF:")
        print(verify_result.stdout)
    else:
        print(f"Error al escribir metadatos: {result.stderr}")

if __name__ == "__main__":
    main()
