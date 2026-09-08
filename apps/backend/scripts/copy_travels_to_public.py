import os, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')

project_root = r"C:\Users\flier\GitHub\viaje-argentina-octubre-2025"
public_dir = os.path.join(project_root, "public")
travels_dir = os.path.join(public_dir, "travels")
os.makedirs(travels_dir, exist_ok=True)

# 1. Copiar HTML de Eslovenia
slov_src = r"F:\2015\Julio\Viaje_Eslovenia_2015.html"
slov_dst = os.path.join(travels_dir, "Viaje_Eslovenia_2015.html")
if os.path.exists(slov_src):
    shutil.copy2(slov_src, slov_dst)
    print(f"Copiado: {slov_dst}")

# 2. Copiar HTML de Argentina
arg_src = r"F:\2025\Octubre\Viaje_Argentina_2025.html"
arg_dst = os.path.join(travels_dir, "Viaje_Argentina_2025.html")
if os.path.exists(arg_src):
    shutil.copy2(arg_src, arg_dst)
    print(f"Copiado: {arg_dst}")

print("¡Archivos HTML copiados a la carpeta public/travels del servidor local!")
print("Ahora puedes acceder mediante:")
print("  - http://localhost:8000/travels/Viaje_Argentina_2025.html")
print("  - http://localhost:8000/travels/Viaje_Eslovenia_2015.html")
