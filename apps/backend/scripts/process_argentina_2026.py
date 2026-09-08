import os
import sys
import io
import shutil
import hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

source_dir = r"F:\Fotos_Organizadas\Viajes\Argentina_2011\2026-01"
target_dir = r"F:\2011\11-Noviembre"
os.makedirs(target_dir, exist_ok=True)

print("--- AUDITORÍA Y CONVERSIÓN DE FOTOS EN Argentina_2011\\2026-01 ---")

if not os.path.exists(source_dir):
    print("La carpeta fuente no existe.")
    sys.exit(0)

try:
    from PIL import Image
    has_pil = True
except ImportError:
    has_pil = False

files = os.listdir(source_dir)
print(f"Total archivos encontrados en 2026-01: {len(files)}")

converted_count = 0
moved_count = 0
skipped_count = 0

for f in files:
    src_path = os.path.join(source_dir, f)
    if not os.path.isfile(src_path):
        continue
        
    base, ext = os.path.splitext(f)
    ext_lower = ext.lower()
    
    # Tag for Argentina 2011
    tag = "Argentina_2011"
    if tag not in base:
        clean_base = f"{base}_{tag}"
    else:
        clean_base = base
        
    if ext_lower == '.gif' and has_pil:
        try:
            # Convert GIF to JPG
            im = Image.open(src_path)
            # Handle animated gifs by taking first frame or converting
            if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                bg = Image.new('RGB', im.size, (255, 255, 255))
                bg.paste(im, mask=im.convert('RGBA'))
                im_rgb = bg
            else:
                im_rgb = im.convert('RGB')
                
            new_fname = f"{clean_base}.jpg"
            dest_path = os.path.join(target_dir, new_fname)
            
            if os.path.exists(dest_path):
                os.remove(src_path)
                skipped_count += 1
            else:
                im_rgb.save(dest_path, 'JPEG', quality=95)
                os.remove(src_path)
                converted_count += 1
        except Exception as e:
            print(f"Error convirtiendo GIF {f}: {e}")
    else:
        # Regular image/file
        new_fname = f"{clean_base}{ext}" if tag not in base else f
        dest_path = os.path.join(target_dir, new_fname)
        
        if os.path.exists(dest_path):
            os.remove(src_path)
            skipped_count += 1
        else:
            shutil.move(src_path, dest_path)
            moved_count += 1

print(f"\nResumen:")
print(f" - GIFs convertidos a JPG y movidos: {converted_count}")
print(f" - Archivos normales movidos: {moved_count}")
print(f" - Duplicados omitidos / eliminados: {skipped_count}")

# Remove source folder if empty
shutil.rmtree(r"F:\Fotos_Organizadas\Viajes\Argentina_2011", ignore_errors=True)
print("Carpeta Argentina_2011 vaciada y eliminada de Viajes.")
