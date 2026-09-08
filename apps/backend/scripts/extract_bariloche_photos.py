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
print(f"Procesando {len(pdf_files)} PDFs de Bariloche...")

photo_counter = 1

def enhance_photo(pil_img):
    # Convert PIL to CV2 BGR
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # 1. Color correction / tint removal (magenta cast reduction)
    # Convert to LAB to handle lighting/contrast separately from color
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # CLAHE on L channel for local contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    # Balance a and b channels to reduce magenta cast
    # In LAB, 'a' goes from green(-) to red/magenta(+), 'b' goes from blue(-) to yellow(+)
    # Since vintage photos have a magenta/red cast, we slightly shift 'a' downwards
    a = cv2.subtract(a, 5)
    
    merged = cv2.merge((l, a, b))
    img_corrected = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    
    # 2. Sharpening
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img_sharpened = cv2.filter2D(img_corrected, -1, kernel)
    
    # Convert back to PIL RGB
    return Image.fromarray(cv2.cvtColor(img_sharpened, cv2.COLOR_BGR2RGB))

for pdf_name in pdf_files:
    pdf_path = os.path.join(my_scans, pdf_name)
    print(f"\nProcesando PDF: {pdf_name}")
    
    pdf = pdfium.PdfDocument(pdf_path)
    for i, page in enumerate(pdf):
        # Render page to high resolution image (scale 2.0 -> ~300 DPI)
        bitmap = page.render(scale=2.0)
        pil_image = bitmap.to_pil()
        
        # Convert to CV2 grayscale for contour detection
        cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # Threshold to find photo frames against white/black background
        _, thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        h_orig, w_orig = cv_img.shape[:2]
        min_area = (w_orig * h_orig) * 0.05 # At least 5% of page area
        
        boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(c)
                # Filter out outer document boundaries if contour is almost the whole page
                if w < w_orig * 0.95 and h < h_orig * 0.95:
                    boxes.append((x, y, w, h))
        
        # If automatic contour extraction didn't cleanly find individual photos (e.g. 6 photos in a grid layout),
        # fallback to grid slicing (3 rows x 2 cols or similar based on standard scan layout).
        if len(boxes) < 2:
            print(f"  [!] Contornos automáticos insuficientes ({len(boxes)}). Aplicando segmentación por cuadrícula 3x2...")
            # Typical grid: 3 rows, 2 columns
            rows, cols = 3, 2
            cell_w = w_orig // cols
            cell_h = h_orig // rows
            for r in range(rows):
                for col in range(cols):
                    x = col * cell_w + int(cell_w * 0.05)
                    y = r * cell_h + int(cell_h * 0.05)
                    w = int(cell_w * 0.90)
                    h = int(cell_h * 0.90)
                    boxes.append((x, y, w, h))
        
        print(f"  Extrayendo {len(boxes)} fotos de la página {i+1}...")
        
        # Sort boxes top-to-bottom, left-to-right
        boxes = sorted(boxes, key=lambda b: (b[1] // 200, b[0]))
        
        for x, y, w, h in boxes:
            # Crop photo
            cropped = pil_image.crop((x, y, x + w, y + h))
            
            # Enhance photo (color correction + sharpening)
            enhanced = enhance_photo(cropped)
            
            # Save
            out_name = f"bariloche_1983_{photo_counter:03d}.jpg"
            out_path = os.path.join(dest_folder, out_name)
            enhanced.save(out_path, quality=95)
            print(f"    Guardada y mejorada: {out_name}")
            photo_counter += 1

print(f"\n¡Proceso finalizado con éxito! Total fotos extraídas y mejoradas: {photo_counter - 1}")
print(f"Ubicación: {dest_folder}")
