import os, sys, time
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

base_dir = r"F:\2025\Octubre\Viaje Familiar de 30 dias por Argentina"
thumbs_dir = os.path.join(base_dir, "_thumbs")
VALID_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG'}

all_images = []
day_dirs = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d != '_thumbs'])

for d in day_dirs:
    dir_path = os.path.join(base_dir, d)
    files = sorted(os.listdir(dir_path))
    for f in files:
        if os.path.splitext(f)[1] in VALID_EXTS:
            all_images.append((d, f, os.path.join(dir_path, f)))

# Probar con y sin exif_transpose para 10 imágenes
print("--- PRUEBA 1: Sin exif_transpose ---")
t0 = time.time()
for idx in range(119, 129):
    _, _, full_path = all_images[idx]
    with Image.open(full_path) as img:
        img.draft('RGB', (512, 512))
        img.thumbnail((512, 512), Image.Resampling.NEAREST)
print(f"10 fotos sin transpose: {time.time()-t0:.3f}s")

print("--- PRUEBA 2: Con thumbnail NEAREST y guardado rápido ---")
t0 = time.time()
for idx in range(119, 129):
    _, _, full_path = all_images[idx]
    out_path = os.path.join(thumbs_dir, f"thumb_{idx}.jpg")
    with Image.open(full_path) as img:
        img.draft('RGB', (512, 512))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((512, 512), Image.Resampling.BILINEAR)
        img.save(out_path, 'JPEG', quality=70)
print(f"10 fotos guardadas: {time.time()-t0:.3f}s")
