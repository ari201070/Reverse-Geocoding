import os
import sys
import time
import cv2
import numpy as np

REF_DIR = r"F:\1983\11-Noviembre"
TARGET_DIR = r"F:\1983\06-Junio"
OUT_DIR = r"F:\1983\06-Junio\Precision_Rostros"

if not os.path.exists("F:\\"):
    REF_DIR = os.path.join("1983", "11-Noviembre")
    TARGET_DIR = os.path.join("1983", "06-Junio")
    OUT_DIR = os.path.join("1983", "06-Junio", "Precision_Rostros")

REF_FILE = "2010-11-14 18.51.13_Scan_Pic0029_gfpgan.jpg"

GFPGAN_REPO = r"C:\Users\flier\AppData\Local\Temp\opencode\GFPGAN"
BASICSR_REPO = r"C:\Users\flier\AppData\Local\Temp\opencode\BasicSR"
MODELS_DIR = r"C:\Users\flier\AppData\Local\Temp\opencode\models"

def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    sys.path.insert(0, GFPGAN_REPO)
    sys.path.insert(0, BASICSR_REPO)
    from gfpgan import GFPGANer

    model_file = os.path.join(MODELS_DIR, "GFPGANv1.4.pth")
    gfpganer = GFPGANer(
        model_path=model_file,
        upscale=1,
        arch="clean",
        channel_multiplier=2,
        bg_upsampler=None,
        device="cpu"
    )

    target_files = sorted([
        f for f in os.listdir(TARGET_DIR) 
        if f.lower().endswith(('.jpg', '.jpeg')) 
        and not f.startswith("precision_")
        and "_mejorada" not in f
    ])
    
    photos_audited = len(target_files)
    photos_enhanced = 0
    total_faces_restored = 0

    print(f"Iniciando procesamiento secuencial general de {photos_audited} imágenes...", flush=True)

    for idx, file_name in enumerate(target_files, 1):
        target_path = os.path.join(TARGET_DIR, file_name)
        img_target = cv2.imread(target_path)
        if img_target is None:
            continue

        h, w = img_target.shape[:2]

        cropped_faces, restored_faces, _ = gfpganer.enhance(
            img_target,
            has_aligned=False,
            only_center_face=False,
            paste_back=False
        )

        n_detected = len(cropped_faces) if cropped_faces else 0
        if n_detected == 0:
            print(f"[{idx:02d}/{photos_audited}] Sin rostros en: {file_name}")
            continue

        # Enfoque general de TODOS los rostros detectados en la foto
        face_helper = gfpganer.face_helper
        face_helper.get_inverse_affine(None)
        final_result = face_helper.paste_faces_to_input_image()
        
        final_out_path = os.path.join(OUT_DIR, f"precision_{file_name}")
        cv2.imwrite(final_out_path, final_result, [cv2.IMWRITE_JPEG_QUALITY, 97])
        photos_enhanced += 1
        total_faces_restored += n_detected
        print(f"[{idx:02d}/{photos_audited}] ¡{n_detected} rostro(s) enfocado(s) en: {file_name}!")

    print("\n==================================================")
    print("PROCESO DE ENFOQUE DE ROSTROS FINALIZADO:")
    print(f" - Fotos auditadas: {photos_audited}")
    print(f" - Fotos con rostros enfocados con éxito: {photos_enhanced}")
    print(f" - Total de rostros restaurados: {total_faces_restored}")
    print("==================================================")

if __name__ == "__main__":
    main()
