import sys
import os
import time
import cv2

sys.path.insert(0, r'C:\Users\flier\AppData\Local\Temp\opencode\Real-ESRGAN')
sys.path.insert(0, r'C:\Users\flier\AppData\Local\Temp\opencode\GFPGAN')

from gfpgan import GFPGANer

models_dir = r'C:\Users\flier\AppData\Local\Temp\opencode\models'

FOLDERS = [
    r"F:\SinFecha_Desconocido\1980\12-Diciembre",
    r"F:\SinFecha_Desconocido\1983\06-Junio",
    r"F:\SinFecha_Desconocido\1983\11-Noviembre",
]

def main():
    print("Loading GFPGAN model...")
    gfpganer = GFPGANer(
        model_path=os.path.join(models_dir, 'GFPGANv1.4.pth'),
        upscale=1, arch='clean', channel_multiplier=2,
        bg_upsampler=None
    )
    print("Ready!\n")

    total = 0
    processed = 0
    skipped = 0
    errors = 0
    total_faces = 0
    start_time = time.time()

    for folder in FOLDERS:
        print(f"\nProcessing: {folder}")
        if not os.path.exists(folder):
            print(f"  Folder not found, skipping")
            continue

        files = sorted([f for f in os.listdir(folder)
                       if f.lower().endswith(('.jpg', '.jpeg', '.png'))
                       and '_gfpgan' not in f
                       and '_restored' not in f])

        for f in files:
            total += 1
            input_path = os.path.join(folder, f)
            base = os.path.splitext(f)[0]
            output_path = os.path.join(folder, f"{base}_gfpgan.jpg")

            if os.path.exists(output_path):
                print(f"  {f} -> skip (already done)")
                skipped += 1
                continue

            print(f"  {f}", end="", flush=True)
            t0 = time.time()

            try:
                img = cv2.imread(input_path)
                if img is None:
                    print(" -> error (can't read)")
                    errors += 1
                    continue

                cropped_faces, restored_faces, restored_img = gfpganer.enhance(
                    img, has_aligned=False, only_center_face=False, paste_back=True
                )

                cv2.imwrite(output_path, restored_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                elapsed = time.time() - t0
                n_faces = len(cropped_faces)
                total_faces += n_faces
                processed += 1
                print(f" -> done ({elapsed:.0f}s, {n_faces} faces)")

            except Exception as e:
                print(f" -> error: {e}")
                errors += 1

    total_time = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"Total photos: {total}")
    print(f"Processed: {processed}")
    print(f"Skipped (already done): {skipped}")
    print(f"Errors: {errors}")
    print(f"Total faces restored: {total_faces}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Average per photo: {total_time/processed:.0f}s" if processed > 0 else "")

if __name__ == "__main__":
    main()
