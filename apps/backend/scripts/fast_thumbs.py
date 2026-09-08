import os, sys, time
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

base_dir = r"F:\2025\Octubre\Viaje Familiar de 30 dias por Argentina"
thumbs_dir = os.path.join(base_dir, "_thumbs")
os.makedirs(thumbs_dir, exist_ok=True)
VALID_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG'}

all_images = []
day_dirs = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d != '_thumbs'])

for d in day_dirs:
    dir_path = os.path.join(base_dir, d)
    files = sorted(os.listdir(dir_path))
    for f in files:
        if os.path.splitext(f)[1] in VALID_EXTS:
            all_images.append((d, f, os.path.join(dir_path, f)))

print(f"Total imágenes a catalogar: {len(all_images)}")

start_time = time.time()
created = 0
skipped = 0
errors = 0

for idx, (day_dir, filename, full_path) in enumerate(all_images):
    out_path = os.path.join(thumbs_dir, f"thumb_{idx}.jpg")
    
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        skipped += 1
        continue

    try:
        with Image.open(full_path) as img:
            img.draft('RGB', (512, 512))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((512, 512), Image.Resampling.BILINEAR)
            img.save(out_path, 'JPEG', quality=70)
            created += 1
    except Exception as e:
        errors += 1

    if (idx + 1) % 250 == 0 or (idx + 1) == len(all_images):
        elapsed = time.time() - start_time
        speed = created / elapsed if elapsed > 0 else 0
        print(f"Progreso: {idx + 1}/{len(all_images)} (Nuevas: {created}, Existentes: {skipped}) a {speed:.1f} fotos/s")

total_time = time.time() - start_time
print(f"\nFinalizado en {total_time:.1f}s. Creadas: {created}, Existentes: {skipped}, Errores: {errors}")
print(f"Total miniaturas en _thumbs: {len(os.listdir(thumbs_dir))}")
