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

def detect_rotation_angle(img_array):
    """Detect rotation angle using multiple methods"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    
    # Method 1: Edge detection + Hough for any angle
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
    
    if lines is not None:
        # Convert to degrees
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90  # Convert to -90 to 90 range
            # Only consider angles that could be photo edges (not perfectly vertical/horizontal)
            if 10 < abs(angle) < 80:
                angles.append(angle)
        
        if angles:
            # Cluster angles and find the most common
            angles = np.array(angles)
            # Round to nearest 5 degrees to cluster similar angles
            rounded = np.round(angles / 5) * 5
            unique, counts = np.unique(rounded, return_counts=True)
            dominant_angle = unique[np.argmax(counts)]
            return dominant_angle
    
    # Method 2: Detect border rotation using minAreaRect on white regions
    _, thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > img_array.shape[0] * img_array.shape[1] * 0.1:
            rect = cv2.minAreaRect(largest)
            angle = rect[-1]
            # Normalize
            if angle < -45:
                angle += 90
            elif angle > 45:
                angle -= 90
            if abs(angle) > 5:  # Only if significant
                return angle
    
    # Method 3: Use image moments
    edges = cv2.Canny(gray, 50, 150)
    # Dilate to connect edges
    kernel = np.ones((5,5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 10000:
            rect = cv2.minAreaRect(largest)
            angle = rect[-1]
            if angle < -45:
                angle += 90
            elif angle > 45:
                angle -= 90
            if abs(angle) > 5:
                return angle
    
    return 0.0

def deskew_image(img, angle):
    """Rotate image to correct skew"""
    if abs(angle) < 2.0:
        return img, False
    
    # Rotate to correct
    return img.rotate(-angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255)), True

def restore_quality(img):
    """Restore photo quality"""
    img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # Light denoise
    denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 5, 5, 7, 15)
    
    pil_img = Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
    
    # Auto contrast
    pil_img = ImageOps.autocontrast(pil_img, cutoff=1)
    
    # Gentle sharpen
    pil_img = pil_img.filter(ImageFilter.SHARPEN)
    
    # Reduce contrast
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.1)
    
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
    """Check if image is already in color"""
    b, g, r = cv2.split(img_array)
    r_var = np.std(r.astype(float))
    g_var = np.std(g.astype(float))
    b_var = np.std(b.astype(float))
    
    rg_diff = abs(r_var - g_var) / max(r_var, g_var)
    rb_diff = abs(r_var - b_var) / max(r_var, b_var)
    
    return (rg_diff > 0.1 or rb_diff > 0.1)

def process_photo(input_path, output_prefix, colorizer):
    """Process a single photo"""
    if os.path.exists(f"{output_prefix}_deoldify.jpg"):
        return False
    
    img = Image.open(input_path)
    img_array = cv2.imread(input_path)
    
    if img_array is None:
        return False
    
    angle = detect_rotation_angle(img_array)
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
                path=temp_path,
                render_factor=35,
                compare=False,
                watermarked=False
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
            
            was_deskewed = process_photo(input_path, output_prefix, colorizer)
            total += 1
            if was_deskewed:
                deskewed += 1
                print(f"  Deskewed: {f}")
    
    print(f"\nTotal: {total}, Deskewed: {deskewed}")

if __name__ == "__main__":
    main()
