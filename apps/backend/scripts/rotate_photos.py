import sys
import os
import cv2
import numpy as np

FOLDERS = [
    r"F:\SinFecha_Desconocido\1980\12-Diciembre",
    r"F:\SinFecha_Desconocido\1983\06-Junio",
    r"F:\SinFecha_Desconocido\1983\11-Noviembre",
]

def show_photo(img, filename, info=""):
    """Show photo with controls"""
    # Resize for display
    h, w = img.shape[:2]
    max_h = 700
    if h > max_h:
        scale = max_h / h
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    
    cv2.imshow("Photo Review", img)
    print(f"\n{filename} ({w}x{h}) {info}")
    print("  [R] Rotate 90° CW  |  [L] Rotate 90° CCW  |  [S] Skip  |  [Q] Quit")

def main():
    print("=" * 60)
    print("PHOTO ROTATION REVIEW TOOL")
    print("=" * 60)
    print("Controls:")
    print("  R = Rotate 90° clockwise")
    print("  L = Rotate 90° counter-clockwise")
    print("  S = Skip (no rotation)")
    print("  Q = Quit")
    print("=" * 60)
    
    cv2.namedWindow("Photo Review", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Photo Review", 800, 700)
    
    changes = {}
    
    for folder in FOLDERS:
        if not os.path.exists(folder):
            continue
        folder_name = os.path.basename(folder)
        print(f"\n--- {folder_name} ---")
        
        files = sorted([f for f in os.listdir(folder)
                       if f.lower().endswith(('.jpg', '.jpeg'))
                       and '_gfpgan' not in f
                       and '_rotated' not in f])
        
        for f in files:
            path = os.path.join(folder, f)
            img = cv2.imread(path)
            if img is None:
                continue
            
            h, w = img.shape[:2]
            orientation = "L" if w > h else "P"
            
            show_photo(img, f, f"[{orientation}]")
            
            while True:
                key = cv2.waitKey(0) & 0xFF
                key = chr(key).lower() if key != 255 else ''
                
                if key == 'r':
                    # Rotate 90° clockwise
                    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    new_path = os.path.join(folder, f"{os.path.splitext(f)[0]}_rotated.jpg")
                    cv2.imwrite(new_path, img)
                    changes[f] = "rotated_cw"
                    print(f"  -> Saved as {os.path.basename(new_path)}")
                    show_photo(img, f, "[ROTATED CW]")
                    break
                    
                elif key == 'l':
                    # Rotate 90° counter-clockwise
                    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    new_path = os.path.join(folder, f"{os.path.splitext(f)[0]}_rotated.jpg")
                    cv2.imwrite(new_path, img)
                    changes[f] = "rotated_ccw"
                    print(f"  -> Saved as {os.path.basename(new_path)}")
                    show_photo(img, f, "[ROTATED CCW]")
                    break
                    
                elif key == 's':
                    print(f"  -> Skipped")
                    break
                    
                elif key == 'q':
                    cv2.destroyAllWindows()
                    print(f"\nProcessed {len(changes)} photos")
                    for name, action in changes.items():
                        print(f"  {name}: {action}")
                    return
    
    cv2.destroyAllWindows()
    print(f"\nDone! Processed {len(changes)} photos")
    for name, action in changes.items():
        print(f"  {name}: {action}")

if __name__ == "__main__":
    main()
