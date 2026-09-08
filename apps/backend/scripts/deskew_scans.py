import os
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

POLAROID_FOLDER = r"F:\SinFecha_Desconocido\1980\12-Diciembre"
REGULAR_FOLDERS = [
    r"F:\SinFecha_Desconocido\1983\06-Junio",
    r"F:\SinFecha_Desconocido\1983\11-Noviembre",
]

def get_skew_angle(img_array):
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    if lines is None:
        return 0.0
    
    angles = []
    for line in lines:
        # OpenCV 5.x returns shape (1, 4) or (4,)
        coords = line.flatten()
        if len(coords) >= 4:
            x1, y1, x2, y2 = coords[:4]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if abs(angle) < 45:
                angles.append(angle)
    
    if not angles:
        return 0.0
    
    return np.median(angles)

def deskew_image(img, angle):
    if abs(angle) < 0.3:
        return img
    
    rotated = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))
    return rotated

def enhance_quality(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img = ImageOps.autocontrast(img, cutoff=1)
    img = img.filter(ImageFilter.SHARPEN)
    
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)
    
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.05)
    
    return img

def process_polaroid(fp):
    img = Image.open(fp)
    img_array = cv2.imread(fp)
    
    if img_array is None:
        return False
    
    angle = get_skew_angle(img_array)
    
    if abs(angle) > 0.3:
        img = deskew_image(img, angle)
    
    img = enhance_quality(img)
    img.save(fp, quality=95, optimize=True)
    return True

def process_regular(fp):
    img = Image.open(fp)
    img_array = cv2.imread(fp)
    
    if img_array is None:
        return False
    
    angle = get_skew_angle(img_array)
    
    if abs(angle) > 0.3:
        img = deskew_image(img, angle)
    
    img = enhance_quality(img)
    img.save(fp, quality=95, optimize=True)
    return True

def process_folder(folder, handler, label):
    if not os.path.exists(folder):
        print(f"  Folder not found: {folder}")
        return 0
    
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    count = 0
    
    for f in files:
        fp = os.path.join(folder, f)
        try:
            if handler(fp):
                count += 1
                print(f"  [OK] {f}")
            else:
                print(f"  [SKIP] {f}")
        except Exception as e:
            print(f"  [ERR] {f}: {e}")
    
    return count

print("=== POLAROID PHOTOS (preserving white borders) ===")
polaroid_count = process_folder(POLAROID_FOLDER, process_polaroid, "polaroid")

print("\n=== REGULAR SCANS ===")
regular_count = 0
for folder in REGULAR_FOLDERS:
    print(f"\nProcessing: {folder}")
    regular_count += process_folder(folder, process_regular, "regular")

print(f"\nTotal processed: {polaroid_count + regular_count}")
print(f"  Polaroids: {polaroid_count}")
print(f"  Regular: {regular_count}")
