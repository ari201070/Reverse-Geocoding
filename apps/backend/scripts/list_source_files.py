import os

SRC_DIR = r"F:\SinFecha_Desconocido\1983\11-Noviembre"
DST_DIR = r"F:\1983\11-Noviembre"

# Fallbacks locales si F:\ no existe
if not os.path.exists("F:\\"):
    SRC_DIR = os.path.join("SinFecha_Desconocido", "1983", "11-Noviembre")
    DST_DIR = os.path.join("1983", "11-Noviembre")

print("==================================================")
print("OBJETIVO 2: CREAR DESTINO Y LISTAR ORIGEN")
print("==================================================")

# 1. Crear carpeta destino si no existe
if not os.path.exists(DST_DIR):
    os.makedirs(DST_DIR)
    print(f"[OK] Carpeta destino creada: {DST_DIR}")
else:
    print(f"[INFO] La carpeta destino ya existia: {DST_DIR}")

# 2. Listar archivos de origen
print(f"\nExplorando origen: {SRC_DIR}")
if os.path.exists(SRC_DIR):
    all_files = os.listdir(SRC_DIR)
    jpg_files = sorted([f for f in all_files if f.lower().endswith(('.jpg', '.jpeg'))])
    
    print(f"Total imagenes (.jpg/.jpeg) encontradas: {len(jpg_files)}")
    print("\nPrimeros 5 archivos:")
    for f in jpg_files[:5]:
        print(f"  - {f}")
else:
    print(f"[ERROR] La carpeta de origen no existe: {SRC_DIR}")

print("\n==================================================")
print("FIN DEL REPORTE")
print("==================================================")
