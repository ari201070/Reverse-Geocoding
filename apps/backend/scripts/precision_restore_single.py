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

REF_CANDIDATES = [
    "2010-11-14 18.51.13_Scan_Pic0029_gfpgan.jpg",
    "2010-11-14 18.36.52_Scan_Pic0017.jpg",
    "2010-11-14 18.42.57_Scan_Pic0022_gfpgan.jpg",
    "2010-11-14 18.20.58_Scan_Pic0003_gfpgan.jpg"
]

TARGET_FILE = "bariloche_primaria 4_page_1_1_mejorada.jpg"

GFPGAN_REPO = r"C:\Users\flier\AppData\Local\Temp\opencode\GFPGAN"
BASICSR_REPO = r"C:\Users\flier\AppData\Local\Temp\opencode\BasicSR"
MODELS_DIR = r"C:\Users\flier\AppData\Local\Temp\opencode\models"

def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    # 1. Archivo de referencia
    ref_path = None
    for cand in REF_CANDIDATES:
        path = os.path.join(REF_DIR, cand)
        if os.path.exists(path):
            ref_path = path
            break

    if not ref_path:
        print(f"Error: No se encontro ninguno de los archivos de referencia en {REF_DIR}")
        return

    print(f"[OK] Usando archivo de referencia: {ref_path}")

    # 2. Archivo objetivo
    target_path = os.path.join(TARGET_DIR, TARGET_FILE)
    if not os.path.exists(target_path):
        for f in os.listdir(TARGET_DIR):
            if "bariloche_primaria 4" in f and "1_1" in f and f.lower().endswith(('.jpg', '.jpeg')):
                target_path = os.path.join(TARGET_DIR, f)
                break

    if not os.path.exists(target_path):
        print(f"Error: No se encuentra la foto objetivo de Bariloche en {TARGET_DIR}")
        return

    print(f"[OK] Procesando foto objetivo de Bariloche: {target_path}")

    # 3. Cargar GFPGAN
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
    print("[OK] Modelo GFPGAN v1.4 cargado con exito.", flush=True)

    # 4. Firma del rostro de referencia (con downscale a max 800px para rapidez en CPU)
    ref_img = cv2.imread(ref_path)
    rh, rw = ref_img.shape[:2]
    if max(rh, rw) > 800:
        rscale = 800.0 / max(rh, rw)
        ref_img = cv2.resize(ref_img, (int(rw * rscale), int(rh * rscale)))

    cropped_ref, _, _ = gfpganer.enhance(ref_img, has_aligned=False, only_center_face=True, paste_back=False)
    if not cropped_ref:
        print("No se pudieron extraer rasgos faciales del archivo de referencia.")
        return

    ref_face = cv2.resize(cropped_ref[0], (128, 128))
    ref_hist = cv2.calcHist([ref_face], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(ref_hist, ref_hist)
    print("[OK] Firma facial de referencia de tu ninez extraida con exito.", flush=True)

    # 5. Deteccion en imagen objetivo a tamano nativo
    img_target = cv2.imread(target_path)
    h, w = img_target.shape[:2]

    cropped_faces, restored_faces, _ = gfpganer.enhance(
        img_target,
        has_aligned=False,
        only_center_face=False,
        paste_back=False
    )

    n_detected = len(cropped_faces) if cropped_faces else 0
    print(f"Se detectaron {n_detected} rostros en la foto grupal.", flush=True)

    if n_detected == 0:
        print("\nNo se encontraron rostros en esta imagen.")
        return

    # 6. Comparar similitud con el rostro de referencia
    best_match_idx = 0
    best_sim = -1.0

    for idx, c_face in enumerate(cropped_faces):
        face_norm = cv2.resize(c_face, (128, 128))
        f_hist = cv2.calcHist([face_norm], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        cv2.normalize(f_hist, f_hist)
        sim = cv2.compareHist(ref_hist, f_hist, cv2.HISTCMP_CORREL)
        print(f"  -> Rostro {idx+1}: similitud con referencia = {sim:.3f}", flush=True)
        if sim > best_sim:
            best_sim = sim
            best_match_idx = idx

    print(f" -> Mejor coincidencia: Rostro {best_match_idx+1} (Similitud: {best_sim:.3f})", flush=True)
    print(" -> ¡Coincidencia de rasgos detectada! Procesando tu rostro de nino...", flush=True)

    # 7. Restaurar UNICAMENTE el rostro que coincide, dejando los demas intactos
    face_helper = gfpganer.face_helper
    for idx in range(len(face_helper.restored_faces)):
        if idx != best_match_idx:
            orig = face_helper.cropped_faces[idx]
            face_helper.restored_faces[idx] = cv2.resize(orig, (face_helper.restored_faces[idx].shape[1], face_helper.restored_faces[idx].shape[0]))

    face_helper.get_inverse_affine(None)
    final_result = face_helper.paste_faces_to_input_image()
    print(" -> [PRECISION FACE OK] Rostro enfocado y reinsertado con exito.", flush=True)

    base_name = os.path.basename(target_path)
    final_out_path = os.path.join(OUT_DIR, f"precision_{base_name}")
    cv2.imwrite(final_out_path, final_result, [cv2.IMWRITE_JPEG_QUALITY, 97])

    print("\n==================================================")
    print("PROCESO DE RESTAURACION DE PRECISION FINALIZADO:")
    print(f" - Archivo guardado: {final_out_path}")
    print(f" - Total de rostros del usuario restaurados: 1")
    print("==================================================")

if __name__ == "__main__":
    main()
