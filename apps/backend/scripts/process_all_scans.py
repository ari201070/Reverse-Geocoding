import os
import re
import cv2
import numpy as np
import fitz  # PyMuPDF

SRC_DIR = r"F:\My Scans"
OUT_DIR = r"F:\Fotos_Organizadas\Scan_Pics_Extraidas"

if not os.path.exists("F:\\"):
    SRC_DIR = "My Scans"
    OUT_DIR = "Scan_Pics_Extraidas"

def natural_color_restore(crop):
    """
    Balance de blancos neutro basado en altas luces / nieve
    y estiramiento de contraste por canal para evitar tonos sepia o púrpuras.
    """
    try:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        bright_mask = gray > np.percentile(gray, 92)
        
        if np.sum(bright_mask) > 50:
            b_ref = np.mean(crop[:, :, 0][bright_mask])
            g_ref = np.mean(crop[:, :, 1][bright_mask])
            r_ref = np.mean(crop[:, :, 2][bright_mask])
            max_ref = max(b_ref, g_ref, r_ref)
            if b_ref > 0 and g_ref > 0 and r_ref > 0:
                scale_b = max_ref / b_ref
                scale_g = max_ref / g_ref
                scale_r = max_ref / r_ref
                b = np.clip(crop[:, :, 0].astype(np.float32) * scale_b, 0, 255)
                g = np.clip(crop[:, :, 1].astype(np.float32) * scale_g, 0, 255)
                r = np.clip(crop[:, :, 2].astype(np.float32) * scale_r, 0, 255)
                wb_img = cv2.merge([b, g, r]).astype(np.uint8)
            else:
                wb_img = crop
        else:
            wb_img = crop
        
        out = np.zeros_like(wb_img, dtype=np.float32)
        for c in range(3):
            ch = wb_img[:, :, c].astype(np.float32)
            p_low = np.percentile(ch, 0.5)
            p_high = np.percentile(ch, 99.5)
            if p_high > p_low:
                out[:, :, c] = np.clip((ch - p_low) * 255.0 / (p_high - p_low), 0, 255)
            else:
                out[:, :, c] = ch
        
        out_bgr = out.astype(np.uint8)
        hsv = cv2.cvtColor(out_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.20, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    except Exception:
        return crop

def extract_bariloche_sheet(img, file_output_dir, pdf_name, page_num):
    h, w = img.shape[:2]
    is_vertical = h > w
    
    if is_vertical:
        # Página vertical (2 columnas x 3 filas)
        boxes = [
            (0, 0, 1050, 1050),
            (1480, 0, 2550, 1050),
            (0, 1150, 1050, 2250),
            (1480, 1100, 2550, 2200),
            (0, 2450, 1050, 3480),
            (1480, 2300, 2550, 3400),
        ]
        rotate_code = cv2.ROTATE_90_COUNTERCLOCKWISE
    else:
        # Página horizontal (3 columnas x 2 filas)
        boxes = [
            (0, 0, 1050, 1050),
            (1150, 0, 2250, 1050),
            (2450, 0, 3480, 1050),
            (0, 1480, 1050, 2550),
            (1150, 1480, 2250, 2550),
            (2450, 1480, 3480, 2550),
        ]
        rotate_code = cv2.ROTATE_90_COUNTERCLOCKWISE
        
    cropped_count = 0
    for idx, (x1, y1, x2, y2) in enumerate(boxes, 1):
        x1 = max(0, min(x1, w))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h))
        y2 = max(0, min(y2, h))
        
        raw_crop = img[y1:y2, x1:x2]
        if raw_crop.size == 0:
            continue
            
        gray = cv2.cvtColor(raw_crop, cv2.COLOR_BGR2GRAY)
        mask = (gray < 240).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            c = max(contours, key=cv2.contourArea)
            bx, by, bw, bh = cv2.boundingRect(c)
            pad = 25  # Inset profundo para barrer cualquier esquina redondeada o borde blanco
            cx1 = max(0, bx + pad)
            cy1 = max(0, by + pad)
            cx2 = min(raw_crop.shape[1], bx + bw - pad)
            cy2 = min(raw_crop.shape[0], by + bh - pad)
            photo = raw_crop[cy1:cy2, cx1:cx2]
        else:
            photo = raw_crop[35:-35, 35:-35]
            
        if photo.size == 0:
            continue
            
        if rotate_code is not None:
            photo = cv2.rotate(photo, rotate_code)
            
        restored = natural_color_restore(photo)
        
        final_filename = f"{pdf_name}_p{page_num+1}_img{idx}.jpg"
        final_path = os.path.join(file_output_dir, final_filename)
        cv2.imwrite(final_path, restored, [cv2.IMWRITE_JPEG_QUALITY, 96])
        cropped_count += 1
        
    return cropped_count

def process_adaptive_contours(img, file_output_dir, pdf_name, page_num):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = cv2.magnitude(grad_x, grad_y)
    bg_mask = (v_channel > 250) & (s_channel < 8) & (grad_mag < 5)
    thresh = np.zeros_like(gray, dtype=np.uint8)
    thresh[~bg_mask] = 255
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total_area = img.shape[0] * img.shape[1]
    min_area = total_area * 0.015
    max_area = total_area * 0.95
    valid_candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if min_area <= area <= max_area:
            valid_candidates.append(c)
    def sort_key(contour):
        x, y, w, h = cv2.boundingRect(contour)
        row = y // 150
        return (row, x)
    valid_candidates = sorted(valid_candidates, key=sort_key)
    cropped_count = 0
    for idx, contour in enumerate(valid_candidates, 1):
        x, y, w, h = cv2.boundingRect(contour)
        pad = 6
        x = max(0, x + pad)
        y = max(0, y + pad)
        w = max(1, w - (pad * 2))
        h = max(1, h - (pad * 2))
        cropped_img = img[y:y+h, x:x+w]
        if cropped_img.size == 0:
            continue
        restored = natural_color_restore(cropped_img)
        final_filename = f"{pdf_name}_p{page_num+1}_img{idx}.jpg"
        final_path = os.path.join(file_output_dir, final_filename)
        cv2.imwrite(final_path, restored, [cv2.IMWRITE_JPEG_QUALITY, 96])
        cropped_count += 1
    return cropped_count

def process_pdf_file(pdf_path):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0].replace(" ", "_")
    print(f"\n==================================================")
    print(f"PROCESANDO ARCHIVO: {pdf_name}.pdf")
    print(f"==================================================")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error al abrir {pdf_path}: {e}")
        return
    total_pages = len(doc)
    file_output_dir = os.path.join(OUT_DIR, pdf_name)
    if not os.path.exists(file_output_dir):
        os.makedirs(file_output_dir)
    cropped_total = 0
    is_bariloche = "bariloche" in pdf_name.lower()
    for page_num in range(total_pages):
        print(f" -> Procesando pagina {page_num+1}/{total_pages}...")
        page = doc[page_num]
        zoom = 300 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        img = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR) if pix.n == 3 else cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
        if is_bariloche:
            count = extract_bariloche_sheet(img, file_output_dir, pdf_name, page_num)
        else:
            count = process_adaptive_contours(img, file_output_dir, pdf_name, page_num)
        cropped_total += count
        print(f"    [OK] Extraidas {count} imagenes de esta pagina.")
    print(f" -> Finalizado: {cropped_total} fotos extraidas del PDF.")

def main():
    if not os.path.exists(SRC_DIR):
        print(f"Error: La carpeta de origen {SRC_DIR} no existe.")
        return
    print(f"Buscando archivos PDF en: {SRC_DIR}")
    pdf_files = []
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    if not pdf_files:
        print("No se encontraron archivos PDF para procesar.")
        return
    print(f"Se encontraron {len(pdf_files)} archivos PDF para procesar.")
    for pdf_path in pdf_files:
        process_pdf_file(pdf_path)
    print("\n==================================================")
    print("¡PROCESAMIENTO COMPLETADO CON ÉXITO!")
    print("==================================================")

if __name__ == "__main__":
    main()
