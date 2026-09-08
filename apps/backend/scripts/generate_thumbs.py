import os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageOps

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

print(f"Total imágenes: {len(all_images)}")

def make_thumb(item):
    idx, full_path, out_path = item
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return idx, True
    try:
        with Image.open(full_path) as img:
            img.draft('RGB', (512, 512))
            img = ImageOps.exif_transpose(img)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((512, 512), Image.Resampling.BILINEAR)
            img.save(out_path, 'JPEG', quality=75)
        return idx, True
    except Exception as e:
        return idx, False

tasks = []
for idx, (day_dir, filename, full_path) in enumerate(all_images):
    out_path = os.path.join(thumbs_dir, f"thumb_{idx}.jpg")
    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        tasks.append((idx, full_path, out_path))

print(f"Tareas pendientes reales: {len(tasks)}")

if tasks:
    t0 = time.time()
    done_count = 0
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(make_thumb, t): t for t in tasks}
        for future in as_completed(futures):
            done_count += 1
            if done_count % 250 == 0 or done_count == len(tasks):
                elapsed = time.time() - t0
                rate = done_count / elapsed if elapsed > 0 else 0
                print(f"Progreso: {done_count}/{len(tasks)} ({rate:.1f} fotos/s)")

print(f"Total final en disco: {len(os.listdir(thumbs_dir))} miniaturas.")
