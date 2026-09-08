import os
import sys
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

TARGETS = [
    r"F:\SinFecha_Desconocido\1980\12-Diciembre",
    r"F:\SinFecha_Desconocido\1983\06-Junio",
    r"F:\SinFecha_Desconocido\1983\11-Noviembre",
]

def enhance_scan(img):
    # Auto-orient based on EXIF
    img = ImageOps.exif_transpose(img)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Auto-contrast
    img = ImageOps.autocontrast(img, cutoff=1)
    
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    
    # Increase contrast slightly
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)
    
    # Increase brightness slightly
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)
    
    return img

def process_folder(folder):
    if not os.path.exists(folder):
        print(f"  Folder not found: {folder}")
        return 0
    
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    count = 0
    
    for f in files:
        fp = os.path.join(folder, f)
        try:
            with Image.open(fp) as img:
                enhanced = enhance_scan(img)
                enhanced.save(fp, quality=95, optimize=True)
                count += 1
                print(f"  [OK] {f}")
        except Exception as e:
            print(f"  [ERR] {f}: {e}")
    
    return count

total = 0
for target in TARGETS:
    print(f"\nProcessing: {target}")
    total += process_folder(target)

print(f"\nTotal enhanced: {total}")
