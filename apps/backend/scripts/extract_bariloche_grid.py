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

def enhance_photo(pil_img):
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    a = cv2.subtract(a, 5)
    merged = cv2.merge((l, a, b))
    img_corrected = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img_sharpened = cv2.filter2D(img_corrected, -1, kernel)
    return Image.fromarray(cv2.cvtColor(img_sharpened, cv2.COLOR_BGR2RGB))

photo_counter = 1

for pdf_name in pdf_files:
    pdf_path = os.path.join(my_scans, pdf_name)
    pdf = pdfium.PdfDocument(pdf_path)
    for i, page in enumerate(pdf):
        bitmap = page.render(scale=2.5) # Higher resolution
        pil_image = bitmap.to_pil()
        w_orig, h_orig = pil_image.size
        
        # Grid 3 rows x 2 cols (6 photos per page as seen in the sample scan)
        rows, cols = 3, 2
        cell_w = w_orig // cols
        cell_h = h_orig // rows
        
        for r in range(rows):
            for col in range(cols):
                # Add slight margin to avoid page borders
                x = col * cell_w + int(cell_w * 0.03)
                y = r * cell_h + int(cell_h * 0.03)
                w = int(cell_w * 0.94)
                h = int(cell_h * 0.94)
                
                cropped = pil_image.crop((x, y, x + w, y + h))
                enhanced = enhance_photo(cropped)
                
                out_name = f"bariloche_1983_{photo_counter:03d}.jpg"
                out_path = os.path.join(dest_folder, out_name)
                enhanced.save(out_path, quality=95)
                photo_counter += 1

print(f"Total fotos extraidas con cuadricula 3x2: {photo_counter - 1}")
