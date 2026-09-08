import os
import cv2
import numpy as np
import fitz

PDF_FOLDER = r"F:\My Scans"
OUTPUT_DIR = r"F:\SinFecha_Desconocido\1983\06-Junio"

def process_pdf(pdf_path, global_idx):
    print(f"\nProcesando: {os.path.basename(pdf_path)}")
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    img = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR) if pix.n == 3 else cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
    
    h, w = img.shape[:2]
    
    rows, cols = 2, 3
    cell_h = h // rows
    cell_w = w // cols
    
    pdf_count = 0
    for r in range(rows):
        for c in range(cols):
            y1 = r * cell_h
            y2 = (r + 1) * cell_h
            x1 = c * cell_w
            x2 = (c + 1) * cell_w
            
            crop = img[y1:y2, x1:x2]
            
            gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            mean_val = np.mean(gray_crop)
            std_val = np.std(gray_crop)
            
            if mean_val < 230 and std_val > 20:
                out_path = os.path.join(OUTPUT_DIR, f"bariloche_1983_{global_idx:03d}.jpg")
                cv2.imwrite(out_path, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
                print(f"  [{global_idx}] {os.path.basename(out_path)} ({crop.shape[1]}x{crop.shape[0]})")
                global_idx += 1
                pdf_count += 1
    
    doc.close()
    print(f"  Extraidas {pdf_count} fotos")
    return global_idx

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    pdfs = sorted([f for f in os.listdir(PDF_FOLDER) if f.startswith("bariloche_primaria") and f.endswith(".pdf")])
    
    print(f"Encontrados {len(pdfs)} PDFs")
    
    global_idx = 1
    for pdf_name in pdfs:
        pdf_path = os.path.join(PDF_FOLDER, pdf_name)
        global_idx = process_pdf(pdf_path, global_idx)
    
    print(f"\nTotal: {global_idx - 1} fotos en {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
