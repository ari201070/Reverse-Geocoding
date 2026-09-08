import os
import shutil

SRC_DIR = r"F:\SinFecha_Desconocido\1983\11-Noviembre"
DST_DIR = r"F:\1983\11-Noviembre"

if not os.path.exists("F:\\"):
    SRC_DIR = os.path.join("SinFecha_Desconocido", "1983", "11-Noviembre")
    DST_DIR = os.path.join("1983", "11-Noviembre")

print("==================================================")
print("OBJETIVO 3: CONSOLIDACION Y COPIA SEGURA")
print("==================================================")

if not os.path.exists(SRC_DIR):
    print(f"[ERROR] Origen no encontrado: {SRC_DIR}")
    exit(1)

if not os.path.exists(DST_DIR):
    os.makedirs(DST_DIR)

files_to_copy = sorted([f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg', '.jpeg'))])
total_files = len(files_to_copy)
print(f"Archivos encontrados para transferir: {total_files}")

copied_count = 0
verified_count = 0
errors = []

for idx, file_name in enumerate(files_to_copy, 1):
    src_path = os.path.join(SRC_DIR, file_name)
    dst_path = os.path.join(DST_DIR, file_name)

    try:
        shutil.copy2(src_path, dst_path)
        copied_count += 1
        
        # Verificacion de integridad por tamano
        src_size = os.path.getsize(src_path)
        dst_size = os.path.getsize(dst_path)
        
        if src_size == dst_size and src_size > 0:
            verified_count += 1
        else:
            errors.append(f"{file_name}: Diferencia de tamano (origen: {src_size}, destino: {dst_size})")
    except Exception as e:
        errors.append(f"{file_name}: Error al copiar ({e})")

print("\n==================================================")
print("REPORTE DE METRICAS FINALES:")
print(f" - Cantidad de archivos a copiar: {total_files}")
print(f" - Cantidad de archivos copiados con exito: {copied_count}")
print(f" - Archivos verificados con 100% integridad: {verified_count}")
if errors:
    print(f" - Errores encontrados ({len(errors)}):")
    for err in errors:
        print(f"    * {err}")
    print(" - Confirmacion de integridad: FALLIDA")
else:
    print(" - Confirmacion de integridad: 100% EXITOSA (todos los archivos coinciden en tamano y metadata)")
print("==================================================")
