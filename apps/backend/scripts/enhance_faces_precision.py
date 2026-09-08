import os
import sys
import time
import cv2
import numpy as np

# Rutas del proyecto en disco F:
DST_DIR = r"F:\1983\06-Junio"
if not os.path.exists("F:\\"):
    DST_DIR = os.path.join("1983", "06-Junio")

# Rutas de modelos
MODELS_DIR = r"C:\Users\flier\AppData\Local\Temp\opencode\models"
GFPGAN_REPO = r"C:\Users\flier\AppData\Local\Temp\opencode\GFPGAN"
BASICSR_REPO = r"C:\Users\flier\AppData\Local\Temp\opencode\BasicSR"

def main():
    if not os.path.exists(DST_DIR):
        print(f"Error: No se encuentra la carpeta de destino: {DST_DIR}")
        return

    print("==================================================")
    print("INICIANDO EXAMEN Y PIPELINE DE ENFOQUE DE ROSTROS")
    print("==================================================")

    # 1. Detectar GFPGAN y CodeFormer
    gfpgan_path = GFPGAN_REPO if os.path.exists(GFPGAN_REPO) else None
    codeformer_path = None

    for root, dirs, files in os.walk("."):
        if "inference_gfpgan.py" in files:
            gfpgan_path = root
        if "inference_codeformer.py" in files:
            codeformer_path = root

    print(f" -> Directorio GFPGAN detectado: {gfpgan_path}")
    print(f" -> Directorio CodeFormer detectado: {codeformer_path}")

    # Cargar modelo GFPGAN v1.4 optimizado en CPU
    sys.path.insert(0, GFPGAN_REPO)
    sys.path.insert(0, BASICSR_REPO)
    from gfpgan import GFPGANer
    model_file = os.path.join(MODELS_DIR, "GFPGANv1.4.pth")
    
    t0 = time.time()
    gfpganer = GFPGANer(
        model_path=model_file,
        upscale=1,
        arch="clean",
        channel_multiplier=2,
        bg_upsampler=None,
        device="cpu"
    )
    print(f" -> Modelo GFPGAN v1.4 cargado en memoria ({time.time()-t0:.1f}s).", flush=True)

    # Listar las 30 fotos mejoradas del lote de Bariloche
    all_files = sorted(os.listdir(DST_DIR))
    target_photos = [f for f in all_files if f.endswith("_mejorada.jpg")]
    
    print(f"Se encontraron {len(target_photos)} imágenes mejoradas para auditar y enfocar rostros.", flush=True)

    enhanced_count = 0
    total_faces_found = 0

    for idx, file_name in enumerate(target_photos, 1):
        base_name, ext = os.path.splitext(file_name)
        out_filename = f"{base_name}_precision_face{ext}"
        out_path = os.path.join(DST_DIR, out_filename)
        
        img_path = os.path.join(DST_DIR, file_name)
        img = cv2.imread(img_path)
        if img is None:
            continue

        h, w = img.shape[:2]
        t_img = time.time()

        try:
            # Súper-resolución previa 1.5x por interpolación Lanczos4 para capturar rostros lejanos/pequeños
            scale = 1.5
            img_scaled = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)
            
            cropped_faces, restored_faces, restored_img_scaled = gfpganer.enhance(
                img_scaled,
                has_aligned=False,
                only_center_face=False,
                paste_back=True
            )
            
            n_faces = len(cropped_faces) if cropped_faces else 0
            
            if n_faces > 0:
                total_faces_found += n_faces
                # Re-escalar al tamaño de la foto mejorada original
                img_final = cv2.resize(restored_img_scaled, (w, h), interpolation=cv2.INTER_AREA)
                cv2.imwrite(out_path, img_final, [cv2.IMWRITE_JPEG_QUALITY, 97])
                print(f" [{idx:02d}/{len(target_photos)}] [PRECISION FACE OK] {file_name} -> {n_faces} rostro(s) enfocado(s) ({time.time()-t_img:.1f}s)", flush=True)
                enhanced_count += 1
            else:
                # Si no tiene rostros, creamos copia precision_face para completitud del catálogo
                cv2.imwrite(out_path, img, [cv2.IMWRITE_JPEG_QUALITY, 97])
                print(f" [{idx:02d}/{len(target_photos)}] [-] {file_name}: Paisaje / sin rostros detectados ({time.time()-t_img:.1f}s)", flush=True)
        except Exception as e:
            print(f" [{idx:02d}/{len(target_photos)}] [ERROR] {file_name}: {e}", flush=True)

    print("\n==================================================", flush=True)
    print("PROCESO DE ENFOQUE DE ROSTROS FINALIZADO:", flush=True)
    print(f" - Fotos auditadas: {len(target_photos)}", flush=True)
    print(f" - Fotos con rostros enfocados con éxito: {enhanced_count}", flush=True)
    print(f" - Total de rostros restaurados: {total_faces_found}", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    main()
