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

def detect_border_angle(img_array):
    """Detect angle using photo borders (white edges)"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    
    # Threshold to find white borders
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return 0.0
    
    # Find the largest contour (should be the photo border)
    largest = max(contours, key=cv2.contourArea)
    
    # Get the minimum area rectangle
    rect = cv2.minAreaRect(largest)
    angle = rect[-1]
    
    # Normalize angle to -45 to 45 range
    if angle < -45:
        angle += 90
    elif angle > 45:
        angle -= 90
    
    return angle

def detect_tilt_angle(img_array):
    """Alternative method: detect tilt using edge detection and Hough"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    
    # Apply blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
    
    # Dilate to connect edges
    kernel = np.ones((3,3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    # Hough lines
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=20)
    
    if lines is None:
        return 0.0
    
    # Only consider near-horizontal lines (within 30 degrees of horizontal)
    angles = []
    for line in lines:
        coords = line.flatten()
        if len(coords) >= 4:
            x1, y1, x2, y2 = coords[:4]
            if abs(x2 - x1) > 50:  # Only consider mostly horizontal lines
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                if abs(angle) < 30:  # Only near-horizontal
                    angles.append(angle)
    
    if not angles:
        return 0.0
    
    # Use median of the near-horizontal angles
    return np.median(angles)

def get_correct_angle(img_array):
    """Get the correct rotation angle using multiple methods"""
    # Try border detection first
    border_angle = detect_border_angle(img_array)
    
    # Try tilt detection
    tilt_angle = detect_tilt_angle(img_array)
    
    # If both agree (same sign), use the more conservative one
    if border_angle * tilt_angle > 0:  # Same sign
        return border_angle if abs(border_angle) < abs(tilt_angle) else tilt_angle
    
    # If they disagree, use the one that's smaller (more conservative)
    return border_angle if abs(border_angle) < abs(tilt_angle) else tilt_angle

def deskew_image(img, angle):
    """Rotate image to correct skew"""
    if abs(angle) < 1.0:
        return img, False
    
    # Rotate to correct (negative of detected angle)
    return img.rotate(-angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255)), True

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
    # Skip if already processed
    if os.path.exists(f"{output_prefix}_deoldify.jpg"):
        return
    
    img = Image.open(input_path)
    img_array = cv2.imread(input_path)
    
    if img_array is None:
        return
    
    # Get correct angle
    angle = get_correct_angle(img_array)
    
    # Deskew
    img, was_deskewed = deskew_image(img, angle)
    
    # Restore
    restored = restore_quality(img)
    
    # Save temp
    temp_path = f"{output_prefix}_temp.jpg"
    restored.save(temp_path, quality=95, optimize=True)
    
    # Check if already color
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
    
    # Clean up
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
