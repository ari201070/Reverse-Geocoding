import os

REF_DIR = r"F:\SinFecha_Desconocido\1983\11-Noviembre"
TARGET_DIR = r"F:\1983\11-Noviembre"

print("==================================================")
print("OBJETIVO 1: VALIDACION FISICA Y MAPEO DE RUTAS")
print("==================================================")

# 1. Verificar carpeta y archivo de referencia
print(f"\n1. Verificando carpeta de referencia: {REF_DIR}")
if os.path.exists(REF_DIR):
    print("   [OK] La carpeta de referencia existe.")
    ref_files = os.listdir(REF_DIR)
    
    # Buscar exactamente o por patron Pic0003
    target_ref = "2010-11-14 18.20.58_Scan_Pic0003_gfpgan.jpg"
    exact_match = os.path.join(REF_DIR, target_ref)
    
    if os.path.exists(exact_match):
        print(f"   [OK] Archivo exacto encontrado: {target_ref}")
    else:
        print(f"   [AVISO] No se encontro exactamente '{target_ref}'.")
        print("   Buscando archivos similares con 'Pic0003':")
        matches = [f for f in ref_files if "Pic0003" in f or "0003" in f]
        for m in matches:
            print(f"     -> {m}")
else:
    print("   [ERROR] La carpeta de referencia no existe.")

# 2. Verificar carpeta objetivo F:\1983\11-Noviembre
print(f"\n2. Verificando carpeta objetivo: {TARGET_DIR}")
if os.path.exists(TARGET_DIR):
    print("   [OK] La carpeta objetivo existe.")
    target_files = sorted(os.listdir(TARGET_DIR))
    print(f"   Total archivos encontrados: {len(target_files)}")
    
    print("\n   Archivos con '0022' o similares en destino:")
    matches_0022 = [f for f in target_files if "0022" in f or "22" in f]
    for m in matches_0022:
        print(f"     -> {m}")
        
    print("\n   Primeros 15 archivos en la carpeta:")
    for f in target_files[:15]:
        print(f"     - {f}")
else:
    print("   [AVISO] La carpeta objetivo F:\\1983\\11-Noviembre no existe.")

print("\n==================================================")
print("FIN DEL REPORTE")
print("==================================================")
