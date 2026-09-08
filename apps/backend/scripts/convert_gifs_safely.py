import os
import sys
import io
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

try:
    from PIL import Image
    has_pil = True
except ImportError:
    has_pil = False

source_dir = r"F:\Fotos_Organizadas\Viajes\Argentina_2011\2026-01"
target_dir = r"F:\2011\11-Noviembre"
os.makedirs(target_dir, exist_ok=True)

print("--- CONVERSIÓN Y TRASLADO SEGURO DE GIFS DE ARGENTINA 2011 ---")

if not os.path.exists(source_dir):
    print("La carpeta fuente no existe.")
    sys.exit(0)

files = os.listdir(source_dir)
print(f"Total archivos en 2026-01: {len(files)}")

converted = 0
skipped = 0

for f in files:
    src_path = os.path.join(source_dir, f)
    if not os.path.isfile(src_path):
        continue
        
    base, ext = os.path.splitext(f)
    ext_lower = ext.lower()
    
    tag = "Argentina_2011"
    clean_base = base if tag in base else f"{base}_{tag}"
    
    if ext_lower == '.gif' and has_pil:
        try:
            with Image.open(src_path) as im:
                if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                    bg = Image.new('RGB', im.size, (255, 255, 255))
                    bg.paste(im, mask=im.convert('RGBA'))
                    im_rgb = bg
                else:
                    im_rgb = im.convert('RGB')
                    
                new_fname = f"{clean_base}.jpg"
                dest_path = os.path.join(target_dir, new_fname)
                
                if os.path.exists(dest_path):
                    skipped += 1
                else:
                    im_rgb.save(dest_path, 'JPEG', quality=95)
                    converted += 1
        except Exception as e:
            print(f"Error procesando {f}: {e}")

print(f"GIFs convertidos y guardados en 2011\\11-Noviembre: {converted}")
print(f"Duplicados omitidos: {skipped}")

shutil.rmtree(source_dir, ignore_errors=True)
# Also remove parent Argentina_2011 if empty
try:
    os.rmdir(r"F:\Fotos_Organizadas\Viajes\Argentina_2011")
except Exception:
    pass
print("Limpieza completada.")
