import sys
import os
import cv2
import numpy as np

FOLDERS = [
    r"F:\SinFecha_Desconocido\1983\06-Junio",
    r"F:\SinFecha_Desconocido\1983\11-Noviembre",
]

def detect_skew(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)
    edges = cv2.Canny(filtered, 30, 200)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=20)
    if lines is None:
        return 0
    angles = []
    for line in lines:
        pts = line.flatten()
        x1, y1, x2, y2 = int(pts[0]), int(pts[1]), int(pts[2]), int(pts[3])
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) < 5 and abs(dy) < 5:
            continue
        angle = np.degrees(np.arctan2(dy, dx))
        length = np.sqrt(dx*dx + dy*dy)
        angles.append((angle, length))
    if not angles:
        return 0
    horiz = [(a, l) for a, l in angles if abs(a) < 15 or abs(a) > 165]
    norm_horiz = []
    for a, l in horiz:
        if a > 90: a -= 180
        elif a < -90: a += 180
        norm_horiz.append((a, l))
    if norm_horiz:
        total_len = sum(l for _, l in norm_horiz)
        avg_angle = sum(a * l for a, l in norm_horiz) / total_len
        return avg_angle
    return 0

def show(img, angle=0, filename="", info=""):
    h, w = img.shape[:2]
    max_h = 700
    if h > max_h:
        scale = max_h / h
        display = cv2.resize(img, (int(w * scale), int(h * scale)))
    else:
        display = img.copy()
    
    # Draw angle indicator
    center = (display.shape[1]//2, 30)
    cv2.putText(display, f"Angle: {angle:+.1f} deg", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(display, filename, (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imshow("Fix", display)

def main():
    print("=" * 60)
    print("ORIENTATION FIX TOOL")
    print("=" * 60)
    print("Controls:")
    print("  [R] Rotate 90° CW      [L] Rotate 90° CCW")
    print("  [1] -5°  [2] -1°       [3] +1°  [4] +5°")
    print("  [A] Apply auto-detect  [S] Save  [N] Skip  [Q] Quit")
    print("=" * 60)
    
    cv2.namedWindow("Fix", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Fix", 900, 750)
    
    for folder in FOLDERS:
        if not os.path.exists(folder):
            continue
        print(f"\n--- {os.path.basename(folder)} ---")
        
        files = sorted([f for f in os.listdir(folder)
                       if f.lower().endswith(('.jpg', '.jpeg'))
                       and '_gfpgan' not in f
                       and '_rotated' not in f
                       and '_fixed' not in f])
        
        for f in files:
            path = os.path.join(folder, f)
            original = cv2.imread(path)
            if original is None:
                continue
            
            h, w = original.shape[:2]
            auto_angle = detect_skew(original)
            current_angle = auto_angle
            current_img = original.copy()
            modified = False
            
            show(current_img, current_angle, f, f"{w}x{h}")
            
            while True:
                key = cv2.waitKey(0) & 0xFF
                key = chr(key).lower() if key != 255 else ''
                
                if key == 'r':
                    current_img = cv2.rotate(current_img, cv2.ROTATE_90_CLOCKWISE)
                    modified = True
                    show(current_img, current_angle, f, "ROTATED CW")
                    
                elif key == 'l':
                    current_img = cv2.rotate(current_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    modified = True
                    show(current_img, current_angle, f, "ROTATED CCW")
                    
                elif key == '1':
                    current_angle -= 5
                    M = cv2.getRotationMatrix2D((w//2, h//2), current_angle, 1.0)
                    current_img = cv2.warpAffine(original, M, (w, h), 
                                                   flags=cv2.INTER_CUBIC,
                                                   borderMode=cv2.BORDER_CONSTANT, 
                                                   borderValue=(255,255,255))
                    modified = True
                    show(current_img, current_angle, f)
                    
                elif key == '2':
                    current_angle -= 1
                    M = cv2.getRotationMatrix2D((w//2, h//2), current_angle, 1.0)
                    current_img = cv2.warpAffine(original, M, (w, h),
                                                   flags=cv2.INTER_CUBIC,
                                                   borderMode=cv2.BORDER_CONSTANT,
                                                   borderValue=(255,255,255))
                    modified = True
                    show(current_img, current_angle, f)
                    
                elif key == '3':
                    current_angle += 1
                    M = cv2.getRotationMatrix2D((w//2, h//2), current_angle, 1.0)
                    current_img = cv2.warpAffine(original, M, (w, h),
                                                   flags=cv2.INTER_CUBIC,
                                                   borderMode=cv2.BORDER_CONSTANT,
                                                   borderValue=(255,255,255))
                    modified = True
                    show(current_img, current_angle, f)
                    
                elif key == '4':
                    current_angle += 5
                    M = cv2.getRotationMatrix2D((w//2, h//2), current_angle, 1.0)
                    current_img = cv2.warpAffine(original, M, (w, h),
                                                   flags=cv2.INTER_CUBIC,
                                                   borderMode=cv2.BORDER_CONSTANT,
                                                   borderValue=(255,255,255))
                    modified = True
                    show(current_img, current_angle, f)
                    
                elif key == 'a':
                    current_angle = detect_skew(current_img)
                    M = cv2.getRotationMatrix2D((w//2, h//2), current_angle, 1.0)
                    current_img = cv2.warpAffine(original, M, (w, h),
                                                   flags=cv2.INTER_CUBIC,
                                                   borderMode=cv2.BORDER_CONSTANT,
                                                   borderValue=(255,255,255))
                    modified = True
                    show(current_img, current_angle, f, "AUTO")
                    
                elif key == 's':
                    if modified:
                        out = os.path.join(folder, f"{os.path.splitext(f)[0]}_fixed.jpg")
                        cv2.imwrite(out, current_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                        print(f"  Saved: {os.path.basename(out)} (angle: {current_angle:+.1f})")
                    break
                    
                elif key == 'n':
                    print(f"  Skipped")
                    break
                    
                elif key == 'q':
                    cv2.destroyAllWindows()
                    return
    
    cv2.destroyAllWindows()
    print("\nDone!")

if __name__ == "__main__":
    main()
