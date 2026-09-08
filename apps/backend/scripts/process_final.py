import sys
import os
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import shutil

deoldify_dir = r'C:\Users\flier\AppData\Local\Temp\opencode\DeOldify'
os.chdir(deoldify_dir)
sys.path.insert(0, deoldify_dir)

from deoldify import device
from deoldify.device_id import DeviceId
from deoldify.visualize import get_image_colorizer
import torch

device.set(DeviceId.CPU)
torch.backends.cudnn.benchmark = False

FOLDERS = [
    r"F:\SinFecha_Desconocido\1980\12-Diciembre",
    r"F:\SinFecha_Desconocido\1983\06-Junio",
    r"F:\SinFecha_Desconocido\1983\11-Noviembre",
]

def detect_skew(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)
    edges = cv2.Canny(filtered, 30, 200)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=20)
    if lines is None:
        return 0
    angles = []
    for line in lines:
        pts = line.flatten()
        x1, y1, x2, y2 = int(pts[0]), int(pts[1]), int(pts[2]), int(pts[3])
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) < 5 and abs(dy) < 5:
            continue
        angle = np.degrees(np.arctan2(dy, dx))
        length = np.sqrt(dx*dx + dy*dy)
        angles.append((angle, length))
    if not angles:
        return 0
    horiz = [(a, l) for a, l in angles if abs(a) < 15 or abs(a) > 165]
    norm_horiz = []
    for a, l in horiz:
        if a > 90: a -= 180
        elif a < -90: a += 180
        norm_horiz.append((a, l))
    if norm_horiz:
        total_len = sum(l for _, l in norm_horiz)
        avg_angle = sum(a * l for a, l in norm_horiz) / total_len
        return avg_angle
    return 0

def deskew_image(img, angle):
    if abs(angle) < 2.0:
        return img, False
    return img.rotate(-angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255)), True

def restore_quality(img):
    img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 5, 5, 7, 15)
    pil_img = Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
    pil_img = ImageOps.autocontrast(pil_img, cutoff=1)
    pil_img = pil_img.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.1)
    img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(img_array, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))

def is_already_color(img_array):
    b, g, r = cv2.split(img_array)
    r_var = np.std(r.astype(float))
    g_var = np.std(g.astype(float))
    b_var = np.std(b.astype(float))
    rg_diff = abs(r_var - g_var) / max(r_var, g_var)
    rb_diff = abs(r_var - b_var) / max(r_var, b_var)
    return (rg_diff > 0.1 or rb_diff > 0.1)

def process_photo(input_path, output_prefix, colorizer):
    if os.path.exists(f"{output_prefix}_deoldify.jpg"):
        return "skip"
    if os.path.exists(f"{output_prefix}_restored.jpg"):
        return "skip"
    
    img = Image.open(input_path)
    img_array = cv2.imread(input_path)
    if img_array is None:
        return "error"
    
    angle = detect_skew(img_array)
    img, was_deskewed = deskew_image(img, angle)
    
    restored = restore_quality(img)
    
    temp_path = f"{output_prefix}_temp.jpg"
    restored.save(temp_path, quality=95, optimize=True)
    
    already_color = is_already_color(img_array)
    
    if already_color:
        final_path = f"{output_prefix}_restored.jpg"
        restored.save(final_path, quality=95, optimize=True)
        result = "restored"
    else:
        try:
            result_path = colorizer.plot_transformed_image(
                path=temp_path, render_factor=35, compare=False, watermarked=False
            )
            if result_path and os.path.exists(result_path):
                final_path = f"{output_prefix}_deoldify.jpg"
                shutil.move(str(result_path), final_path)
                result = "colorized"
            else:
                result = "error"
        except Exception as e:
            print(f"  [ERR] {e}")
            result = "error"
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    if was_deskewed:
        result += " (deskewed)"
    
    return result

def main():
    print("Loading DeOldify...")
    colorizer = get_image_colorizer(artistic=True)
    print("Ready!\n")
    
    stats = {"skip": 0, "colorized": 0, "restored": 0, "error": 0, "deskewed": 0}
    
    for folder in FOLDERS:
        print(f"\nProcessing: {folder}")
        if not os.path.exists(folder):
            continue
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        for f in files:
            if '_deoldify' in f or '_temp' in f or '_restored' in f:
                continue
            input_path = os.path.join(folder, f)
            output_prefix = os.path.join(folder, os.path.splitext(f)[0])
            print(f"  {f}", end="")
            result = process_photo(input_path, output_prefix, colorizer)
            print(f" -> {result}")
            for key in stats:
                if key in result:
                    stats[key] += 1
    
    print(f"\n=== Summary ===")
    print(f"Colorized: {stats['colorized']}")
    print(f"Restored (already color): {stats['restored']}")
    print(f"Skipped (already done): {stats['skip']}")
    print(f"Deskewed: {stats['deskewed']}")
    print(f"Errors: {stats['error']}")

if __name__ == "__main__":
    main()
