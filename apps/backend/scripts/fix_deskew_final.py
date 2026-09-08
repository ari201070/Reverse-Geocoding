import sys
import os
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

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

def score_rotation(img_array, angle):
    h, w = img_array.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img_array, M, (w, h), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    h2, w2 = edges.shape
    border_top = edges[:int(h2*0.1), :]
    border_bottom = edges[int(h2*0.9):, :]
    border_left = edges[:, :int(w2*0.1)]
    border_right = edges[:, int(w2*0.9):]
    score = (np.mean(border_top) + np.mean(border_bottom) +
             np.mean(border_left) + np.mean(border_right))
    return score

def find_best_rotation(img_array):
    angles = np.arange(-45, 46, 1)
    best_angle = 0
    best_score = 0
    for angle in angles:
        score = score_rotation(img_array, angle)
        if score > best_score:
            best_score = score
            best_angle = angle
    return best_angle

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
        return False
    img = Image.open(input_path)
    img_array = cv2.imread(input_path)
    if img_array is None:
        return False
    angle = find_best_rotation(img_array)
    print(f"    Detected angle: {angle}")
    img, was_deskewed = deskew_image(img, angle)
    restored = restore_quality(img)
    temp_path = f"{output_prefix}_temp.jpg"
    restored.save(temp_path, quality=95, optimize=True)
    already_color = is_already_color(img_array)
    if already_color:
        final_path = f"{output_prefix}_restored.jpg"
        restored.save(final_path, quality=95, optimize=True)
    else:
        try:
            result_path = colorizer.plot_transformed_image(
                path=temp_path, render_factor=35, compare=False, watermarked=False
            )
            if result_path and os.path.exists(result_path):
                import shutil
                final_path = f"{output_prefix}_deoldify.jpg"
                shutil.move(str(result_path), final_path)
        except Exception as e:
            print(f"  [ERR] {e}")
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return was_deskewed

def main():
    print("Loading DeOldify...")
    colorizer = get_image_colorizer(artistic=True)
    print("Ready!\n")
    total = 0
    deskewed = 0
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
            print(f"  {f}")
            was_deskewed = process_photo(input_path, output_prefix, colorizer)
            total += 1
            if was_deskewed:
                deskewed += 1
    print(f"\nTotal: {total}, Deskewed: {deskewed}")

if __name__ == "__main__":
    main()
