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
    """Rotate image to correct skew - only if significant"""
    if abs(angle) < 1.5:  # Only correct if >1.5 degrees
        return img, False
    return img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255)), True

def restore_quality(img):
    """Restore photo quality - more conservative approach"""
    # Convert to OpenCV format
    img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # Light denoise
    denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 5, 5, 7, 15)
    
    # Convert back to PIL
    pil_img = Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
    
    # Auto contrast - less aggressive
    pil_img = ImageOps.autocontrast(pil_img, cutoff=1)
    
    # Gentle sharpen
    pil_img = pil_img.filter(ImageFilter.SHARPEN)
    
    # Reduce contrast enhancement (was 1.3, now 1.1)
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.1)
    
    # NO brightness enhancement - keep original
    
    # Gentle CLAHE
    img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(img_array, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    return Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))

def is_already_color(img_array):
    """Check if image is already in color (not grayscale/sepia)"""
    b, g, r = cv2.split(img_array)
    # Check color variance - if channels are very similar, it's likely grayscale
    r_var = np.std(r.astype(float))
    g_var = np.std(g.astype(float))
    b_var = np.std(b.astype(float))
    
    # Check if color channels differ significantly
    rg_diff = abs(r_var - g_var) / max(r_var, g_var)
    rb_diff = abs(r_var - b_var) / max(r_var, b_var)
    
    return (rg_diff > 0.1 or rb_diff > 0.1)

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
    
    # Check if already color
    already_color = is_already_color(img_array)
    
    print(f"  Step 1: Deskewing...")
    angle = get_skew_angle(img_array)
    img, was_deskewed = deskew_image(img, angle)
    if was_deskewed:
        print(f"    Corrected {angle:.1f} degrees")
    else:
        print(f"    No correction needed (angle: {angle:.1f}°)")
    
    print(f"  Step 2: Restoring quality...")
    restored = restore_quality(img)
    
    # Save restored version (intermediate)
    temp_path = f"{output_prefix}_temp.jpg"
    restored.save(temp_path, quality=95, optimize=True)
    
    if already_color:
        print(f"  Step 3: Already color - skipping DeOldify, keeping restored version")
        final_path = f"{output_prefix}_restored.jpg"
        restored.save(final_path, quality=95, optimize=True)
    else:
        print(f"  Step 3: Colorizing with DeOldify...")
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
            if '_deoldify' in f or '_temp' in f or '_restored' in f:
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
