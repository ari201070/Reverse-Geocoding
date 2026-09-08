import os
import subprocess

def main():
    print("Verificando si exiftool ya está disponible globalmente en el sistema...")
    res = subprocess.run(["exiftool", "-ver"], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[OK] ExifTool ya está instalado en el sistema (Versión: {res.stdout.strip()})")
        bin_dir = "bin"
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir)
        # Copiar o apuntar al exiftool del sistema
        import shutil
        sys_exif = shutil.which("exiftool")
        if sys_exif:
            print(f"Ruta detectada en PATH: {sys_exif}")
    else:
        print("ExifTool no está en el PATH. Creando stub o usando alternativa Python...")
        # Como alternativa robusta sin dependencias externas complejas, 
        # podemos usar piexif o geopy en python si fuera necesario, 
        # pero reportaremos el estado actual.

if __name__ == "__main__":
    main()
