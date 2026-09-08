import os
import sys
import io
import pypdfium2 as pdfium
import cv2
import numpy as np
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

my_scans = r"F:\My Scans"
dest_folder = r"F:\1983"
os.makedirs(dest_folder, exist_ok=True)

pdf_files = sorted([f for f in os.listdir(my_scans) if "bariloche" in f.lower() and f.endswith(".pdf")])

def enhance_photo_pro(pil_img):
    # Convert PIL to CV2 BGR
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # 1. Advanced Color Correction (Neutralize magenta cast / white balance)
    # Convert to LAB
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Adaptive CLAHE for high local contrast on L channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    # Neutralize magenta/red cast: shift 'a' channel down toward green/neutral
    # and slightly boost 'b' channel if needed
    a = cv2.subtract(a, 8)
    
    merged = cv2.merge((l, a, b))
    img_corrected = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    
    # 2. Denoising to remove scan grain and artifacts
    denoised = cv2.fastNlMeansDenoisingColored(img_corrected, None, 10, 10, 7, 21)
    
    # 3. Unsharp Masking for crisp, clear details
    gaussian = cv2.GaussianBlur(denoised, (0, 0), 2.0)
    sharpened = cv2.addWeighted(denoised, 1.5, gaussian, -0.5, 0)
    
    return Image.fromarray(cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB))

photo_counter = 1

for pdf_name in pdf_files:
    pdf_path = os.path.join(my_scans, pdf_name)
    pdf = pdfium.PdfDocument(pdf_path)
    for i, page in enumerate(pdf):
        # Render at 300 DPI (scale 3.0)
        bitmap = page.render(scale=3.0)
        pil_image = bitmap.to_pil()
        cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale and threshold to detect photo bounding boxes against white background
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # Threshold: paper background is very bright (>220)
        _, thresh = cv2.threshold(gray, 215, 255, cv2.THRESH_BINARY_INV)
        
        # Morphological closing to merge slight gaps inside photos
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find external contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        h_orig, w_orig = cv_img.shape[:2]
        min_area = (w_orig * h_orig) * 0.03 # At least 3% of page area per photo
        
        boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(c)
                # Ensure it's not capturing the whole page border
                if w < w_orig * 0.98 and h < h_orig * 0.98:
                    # Add small padding inward to eliminate white card borders completely
                    pad = 10
                    x_p = max(0, x + pad)
                    y_p = max(0, y + pad)
                    w_p = max(10, w - (pad * 2))
                    h_p = max(10, h - (pad * 2))
                    boxes.append((x_p, y_p, w_p, h_p))
        
        # Sort boxes top-to-bottom, left-to-right (tolerance in Y of ~50 pixels)
        boxes = sorted(boxes, key=lambda b: (b[1] // 100, b[0]))
        
        # If we didn't find exactly 6 or found too few/many due to background noise, fallback to intelligent sub-grid regions
        if len(boxes) != 6:
            print(f"  [!] {pdf_name}: Encontrados {len(boxes)} contornos. Refinando con análisis de subregiones...")
            boxes = []
            rows, cols = 3, 2
            cell_w = w_orig // cols
            cell_h = h_orig // rows
            for r in range(rows):
                for col in range(cols):
                    # Precise crop inside each grid cell to find the exact photo borders
                    sub_cell = gray[r*cell_h:(r+1)*cell_h, col*cell_w:(col+1)*cell_w]
                    _, sub_thresh = cv2.threshold(sub_cell, 210, 255, cv2.THRESH_BINARY_INV)
                    sub_contours, _ = cv2.findContours(sub_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if sub_contours:
                        # Find largest contour in cell
                        c_max = max(sub_contours, key=cv2.contourArea)
                        if cv2.contourArea(c_max) > (cell_w * cell_h * 0.1):
                            cx, cy, cw, ch = cv2.boundingRect(c_max)
                            boxes.append((col*cell_w + cx + 5, r*cell_h + cy + 5, cw - 10, ch - 10))
                        else:
                            # Default fallback box in cell
                            boxes.append((col*cell_w + int(cell_w*0.05), r*cell_h + int(cell_h*0.05), int(cell_w*0.9), int(cell_h*0.9)))
                    else:
                        boxes.append((col*cell_w + int(cell_w*0.05), r*cell_h + int(cell_h*0.05), int(cell_w*0.9), int(cell_h*0.9)))

        print(f"  Extrayendo y mejorando {len(boxes)} fotos reales de {pdf_name}...")
        for x, y, w, h in boxes:
            cropped = pil_image.crop((x, y, x + w, y + h))
            enhanced = enhance_photo_pro(cropped)
            
            out_name = f"bariloche_1983_{photo_counter:03d}.jpg"
            out_path = os.path.join(dest_folder, out_name)
            enhanced.save(out_path, quality=98)
            photo_counter += 1

print(f"\n¡Extracción y mejora profesional completada con éxito! Total fotos limpias: {photo_counter - 1}")
print(f"Ubicación: {dest_folder}")
