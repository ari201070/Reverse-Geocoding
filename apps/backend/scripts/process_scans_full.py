import sys
import os
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# DeOldify setup
deoldify_dir = r'C:\Users\flier\AppData\Local\Temp\opencode\DeOldify'
os.chdir(deoldify_dir)
sys.path.insert(0, deoldify_dir)

from deoldify import device
from deoldify.device_id import DeviceId
from deoldify.visualize import get_image_colorizer
import torch

device.set(DeviceId.CPU)
torch.backends.cudnn.benchmark = False

# Folders to process
FOLDERS = [
    r"F:\SinFecha_Desconocido\1980\12-Diciembre",
    r"F:\SinFecha_Desconocido\1983\06-Junio",
    r"F:\SinFecha_Desconocido\1983\11-Noviembre",
]

def get_skew_angle(img_array):
    """Detect skew angle using Hough transform"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    if lines is None:
        return 0.0
    
    angles = []
    for line in lines:
        coords = line.flatten()
        if len(coords) >= 4:
            x1, y1, x2, y2 = coords[:4]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if abs(angle) < 45:
                angles.append(angle)
    
    return np.median(angles) if angles else 0.0

def deskew_image(img, angle):
    """Rotate image to correct skew"""
    if abs(angle) < 0.3:
        return img
    return img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))

def restore_quality(img):
    """Restore photo quality: denoise, sharpen, improve contrast"""
    # Convert to OpenCV format
    img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
    
    # Convert back to PIL
    pil_img = Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
    
    # Auto contrast
    pil_img = ImageOps.autocontrast(pil_img, cutoff=2)
    
    # Sharpen
    pil_img = pil_img.filter(ImageFilter.SHARPEN)
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.3)
    
    # Enhance brightness slightly
    enhancer = ImageEnhance.Brightness(pil_img)
    pil_img = enhancer.enhance(1.1)
    
    # Additional CLAHE enhancement
    img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(img_array, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    return Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))

def process_photo(input_path, output_prefix, colorizer):
    """Full processing pipeline for a photo"""
    # Skip if already processed
    if os.path.exists(f"{output_prefix}_deoldify.jpg"):
        print(f"  [SKIP] Already processed")
        return
    
    # Read image
    img = Image.open(input_path)
    img_array = cv2.imread(input_path)
    
    if img_array is None:
        print(f"  [ERR] Could not read image")
        return
    
    print(f"  Step 1: Deskewing...")
    angle = get_skew_angle(img_array)
    if abs(angle) > 0.3:
        img = deskew_image(img, angle)
        print(f"    Corrected {angle:.1f} degrees")
    else:
        print(f"    No significant skew detected")
    
    print(f"  Step 2: Restoring quality...")
    restored = restore_quality(img)
    
    # Save restored version (intermediate)
    temp_path = f"{output_prefix}_temp.jpg"
    restored.save(temp_path, quality=95, optimize=True)
    
    print(f"  Step 3: Colorizing...")
    try:
        result_path = colorizer.plot_transformed_image(
            path=temp_path,
            render_factor=35,
            compare=False,
            watermarked=False
        )
        
        if result_path and os.path.exists(result_path):
            import shutil
            final_path = f"{output_prefix}_deoldify.jpg"
            shutil.move(str(result_path), final_path)
            print(f"  Saved: {final_path}")
        else:
            print(f"  [ERR] Colorization failed")
    except Exception as e:
        print(f"  [ERR] Colorization error: {e}")
    
    # Clean up temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)

def main():
    print("Loading DeOldify colorizer...")
    colorizer = get_image_colorizer(artistic=True)
    print("Colorizer loaded!\n")
    
    total_processed = 0
    
    for folder in FOLDERS:
        print(f"\n{'='*60}")
        print(f"Processing: {folder}")
        print(f"{'='*60}")
        
        if not os.path.exists(folder):
            print(f"  Folder not found!")
            continue
        
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        for f in files:
            if '_deoldify' in f or '_temp' in f:
                continue
            
            input_path = os.path.join(folder, f)
            output_prefix = os.path.join(folder, os.path.splitext(f)[0])
            
            print(f"\nProcessing: {f}")
            process_photo(input_path, output_prefix, colorizer)
            total_processed += 1
    
    print(f"\n{'='*60}")
    print(f"Total photos processed: {total_processed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
