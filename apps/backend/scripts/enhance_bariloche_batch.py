import os
import cv2
import numpy as np

BASE_DIR = r"F:\Fotos_Organizadas\Scan_Pics_Extraidas"
FOLDERS = [f"bariloche_primaria_{i}" for i in range(1, 6)]

def enhance_photo(img):
    """
    Restaura color, balance de blancos, contraste y aplica enfoque
    adaptativo según el nivel de desenfoque de cada foto.
    No modifica dimensiones ni posición.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Medir nivel de desenfoque / nitidez (Varianza del Laplaciano)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    needs_strong_focus = lap_var < 40.0
    needs_mild_focus = 40.0 <= lap_var < 85.0
    
    # 2. Corrección y balance de color por canal (neutralizar velo magenta 80s)
    stretched = np.zeros_like(img, dtype=np.float32)
    for c in range(3):
        ch = img[:, :, c].astype(np.float32)
        p_low = np.percentile(ch, 1.0)
        p_high = np.percentile(ch, 99.0)
        if p_high > p_low:
            stretched[:, :, c] = np.clip((ch - p_low) * 255.0 / (p_high - p_low), 0, 255)
        else:
            stretched[:, :, c] = ch
            
    balanced = stretched.astype(np.uint8)
    
    # Neutralización de medios tonos
    b, g, r = cv2.split(balanced.astype(np.float32))
    mask = (gray > 40) & (gray < 220)
    if np.sum(mask) > 100:
        mb, mg, mr = np.mean(b[mask]), np.mean(g[mask]), np.mean(r[mask])
    else:
        mb, mg, mr = np.mean(b), np.mean(g), np.mean(r)
    target = (mb + mg + mr) / 3.0
    b = np.clip(b * (target / max(mb, 1)), 0, 255)
    g = np.clip(g * (target / max(mg, 1)), 0, 255)
    r = np.clip(r * (target / max(mr, 1)), 0, 255)
    neutral = cv2.merge([b, g, r]).astype(np.uint8)
    
    # 3. Realce de saturación y vivacidad natural en espacio HSV
    hsv = cv2.cvtColor(neutral, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.30, 0, 255)
    color_enhanced = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    # 4. Mejora de contraste adaptativo (CLAHE en canal L de espacio LAB)
    lab = cv2.cvtColor(color_enhanced, cv2.COLOR_BGR2LAB)
    l, a, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8))
    l = clahe.apply(l)
    contrast_img = cv2.cvtColor(cv2.merge([l, a, b_ch]), cv2.COLOR_LAB2BGR)
    
    # 5. Enfoque adaptativo inteligente
    if needs_strong_focus:
        # Foto desenfocada: máscara de desenfoque bilateral + realce de bordes
        smooth = cv2.bilateralFilter(contrast_img, 7, 50, 50)
        unsharp = cv2.addWeighted(contrast_img, 1.6, smooth, -0.6, 0)
        kernel = np.array([[0, -0.5, 0], [-0.5, 3.0, -0.5], [0, -0.5, 0]])
        final = cv2.filter2D(unsharp, -1, kernel)
        treatment = f"Enfoque fuerte + Coloración (desenfoque={lap_var:.1f})"
    elif needs_mild_focus:
        # Foto con desenfoque medio: realce suave de nitidez
        smooth = cv2.GaussianBlur(contrast_img, (0, 0), 1.2)
        final = cv2.addWeighted(contrast_img, 1.4, smooth, -0.4, 0)
        treatment = f"Enfoque moderado + Coloración (desenfoque={lap_var:.1f})"
    else:
        # Foto nítida: solo coloración y microcontraste sutil sin forzar grano
        smooth = cv2.GaussianBlur(contrast_img, (0, 0), 0.8)
        final = cv2.addWeighted(contrast_img, 1.15, smooth, -0.15, 0)
        treatment = f"Solo Coloración / Contraste (nítida={lap_var:.1f})"
        
    return final, treatment

def main():
    total_processed = 0
    print("=" * 70)
    print("PROCESAMIENTO DE MEJORA DE CALIDAD (FOTOS BARILOCHE 1 A 5)")
    print("Manteniendo originales intactas - Sin rotar ni alterar tamaños")
    print("=" * 70)
    
    for folder in FOLDERS:
        folder_path = os.path.join(BASE_DIR, folder)
        if not os.path.exists(folder_path):
            print(f"Carpeta no encontrada: {folder_path}")
            continue
            
        print(f"\n--- Carpeta: {folder} ---")
        files = sorted([f for f in os.listdir(folder_path) 
                       if f.lower().endswith(('.jpg', '.jpeg', '.png')) 
                       and not f.endswith("_mejorada.jpg")])
                       
        for fname in files:
            src_path = os.path.join(folder_path, fname)
            img = cv2.imread(src_path)
            if img is None:
                print(f"  [ERROR] No se pudo leer {fname}")
                continue
                
            enhanced, treatment = enhance_photo(img)
            
            # Guardar copia mejorada junto a la original
            base_name, ext = os.path.splitext(fname)
            out_fname = f"{base_name}_mejorada{ext}"
            out_path = os.path.join(folder_path, out_fname)
            
            cv2.imwrite(out_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 96])
            print(f"  [OK] {fname} ({img.shape[1]}x{img.shape[0]} px)")
            print(f"       -> Copia: {out_fname} | Tratamiento: {treatment}")
            total_processed += 1
            
    print("\n" + "=" * 70)
    print(f"COMPLETADO: {total_processed} fotos mejoradas creadas con éxito.")
    print("=" * 70)

if __name__ == "__main__":
    main()
