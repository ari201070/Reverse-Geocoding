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

print("=" * 70)
print("DETECTANDO ANGULOS DE TODAS LAS FOTOS")
print("=" * 70)

for folder in FOLDERS:
    if not os.path.exists(folder):
        continue
    folder_name = os.path.basename(folder)
    print(f"\n--- {folder_name} ---")
    
    files = sorted([f for f in os.listdir(folder)
                   if f.lower().endswith(('.jpg', '.jpeg'))
                   and '_gfpgan' not in f
                   and '_rotated' not in f
                   and '_fixed' not in f])
    
    for f in files:
        path = os.path.join(folder, f)
        img = cv2.imread(path)
        if img is None:
            continue
        h, w = img.shape[:2]
        angle = detect_skew(img)
        orient = "L" if w > h else "P"
        flag = " *** NEEDS FIX" if abs(angle) > 3.0 else ""
        print(f"  {f}: {w}x{h} [{orient}] angle={angle:+.1f}{flag}")

print("\n" + "=" * 70)
print("Para corregir fotos, decime los nombres y el angulo/rotacion")
print("=" * 70)
