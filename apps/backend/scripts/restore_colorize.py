import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

def restore_photo(img):
    """Restore old photo: remove noise, sharpen, improve contrast"""
    # Denoise
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    
    # Convert to PIL for better sharpening
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
    
    # Convert back to OpenCV format
    restored = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # Additional contrast enhancement using CLAHE
    lab = cv2.cvtColor(restored, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    return enhanced

def remove_sepia(img):
    """Remove sepia tone and convert to neutral grayscale"""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray_enhanced = clahe.apply(gray)
    
    # Convert back to 3 channel
    return cv2.cvtColor(gray_enhanced, cv2.COLOR_GRAY2BGR)

def colorize_basic(img):
    """Basic colorization using luminance-based approach"""
    # Convert to float for calculations
    img_float = img.astype(np.float32) / 255.0
    
    # Calculate luminance
    gray = cv2.cvtColor((img_float * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    
    # Create color channels based on luminance
    # Warm tones for skin (higher luminance = more warm)
    # Cool tones for shadows (lower luminance = more cool)
    
    # Initialize channels
    b_channel = np.zeros_like(gray)
    g_channel = np.zeros_like(gray)
    r_channel = np.zeros_like(gray)
    
    # Skin tones (warm)
    skin_mask = (gray > 0.4) & (gray < 0.8)
    r_channel[skin_mask] = 0.6 + gray[skin_mask] * 0.3
    g_channel[skin_mask] = 0.4 + gray[skin_mask] * 0.2
    b_channel[skin_mask] = 0.3 + gray[skin_mask] * 0.2
    
    # Background (cooler)
    bg_mask = gray > 0.3
    b_channel[bg_mask] = np.maximum(b_channel[bg_mask], 0.2 + gray[bg_mask] * 0.15)
    g_channel[bg_mask] = np.maximum(g_channel[bg_mask], 0.3 + gray[bg_mask] * 0.1)
    
    # Dark areas (blue-ish)
    dark_mask = gray < 0.3
    b_channel[dark_mask] = 0.15 + gray[dark_mask] * 0.2
    g_channel[dark_mask] = 0.1 + gray[dark_mask] * 0.15
    r_channel[dark_mask] = 0.1 + gray[dark_mask] * 0.1
    
    # Clamp values
    r_channel = np.clip(r_channel, 0, 1)
    g_channel = np.clip(g_channel, 0, 1)
    b_channel = np.clip(b_channel, 0, 1)
    
    # Stack channels
    colorized = np.stack([b_channel, g_channel, r_channel], axis=-1)
    
    # Blend with original grayscale for more natural look
    gray_3ch = np.stack([gray, gray, gray], axis=-1)
    result = colorized * 0.6 + gray_3ch * 0.4
    
    # Convert back to uint8
    return (result * 255).astype(np.uint8)

def process_photo(input_path, output_prefix):
    """Full restoration and colorization pipeline"""
    # Read image
    img = cv2.imread(input_path)
    if img is None:
        print(f"Error reading: {input_path}")
        return
    
    print(f"Processing: {input_path}")
    
    # Step 1: Remove sepia and get neutral grayscale
    neutral = remove_sepia(img)
    cv2.imwrite(f"{output_prefix}_restored.jpg", neutral, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  Saved: {output_prefix}_restored.jpg")
    
    # Step 2: Colorize
    colorized = colorize_basic(neutral)
    cv2.imwrite(f"{output_prefix}_colorized.jpg", colorized, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  Saved: {output_prefix}_colorized.jpg")
    
    # Step 3: Enhanced version (sharper)
    enhanced = restore_photo(img)
    cv2.imwrite(f"{output_prefix}_enhanced.jpg", enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  Saved: {output_prefix}_enhanced.jpg")

# Process the photos
base = r"F:\SinFecha_Desconocido\1983\11-Noviembre"

photo1 = f"{base}\\2010-11-14 18.12.09_Scan_Pic0001.jpg"
photo2 = f"{base}\\2010-11-14 18.57.04_Casamiento Papa y Mama.jpg"

process_photo(photo1, f"{base}\\familia_fuente")
process_photo(photo2, f"{base}\\casamiento")

print("\nDone!")
