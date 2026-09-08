import os
import cv2
import numpy as np
import fitz  # PyMuPDF

def main():
    pdf_path = "bariloche_primaria 1.pdf"
    
    if not os.path.exists(pdf_path):
        for root, dirs, files in os.walk("F:\\"):
            if "bariloche_primaria 1.pdf" in files:
                pdf_path = os.path.join(root, "bariloche_primaria 1.pdf")
                break
                
    if not os.path.exists(pdf_path):
        print(f"Error: No se encontro '{pdf_path}'.")
        return

    print(f"Abriendo: {pdf_path}")
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    img = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR) if pix.n == 3 else cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    min_area = img.shape[0] * img.shape[1] * 0.02
    valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]
    
    valid_contours = sorted(valid_contours, key=lambda c: (cv2.boundingRect(c)[1] // 100, cv2.boundingRect(c)[0]))
    
    print(f"Detectadas {len(valid_contours)} fotos individuales validas.")
    
    output_dir = r"F:\2023\05-Mayo\Bariloche_Recortadas"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for idx, c in enumerate(valid_contours, 1):
        x, y, w, h = cv2.boundingRect(c)
        
        padding = 3
        crop_x = max(0, x + padding)
        crop_y = max(0, y + padding)
        crop_w = max(1, w - (padding * 2))
        crop_h = max(1, h - (padding * 2))
        
        crop = img[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        
        out_path = os.path.join(output_dir, f"bariloche_1983_crop_{idx}.jpg")
        cv2.imwrite(out_path, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"  [CROP OK] {out_path} ({crop_w}x{crop_h} px)")
        
    print("\nProcesamiento terminado con exito.")

if __name__ == "__main__":
    main()
