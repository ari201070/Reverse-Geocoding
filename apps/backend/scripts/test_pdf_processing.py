import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

try:
    import fitz # PyMuPDF
    import cv2
    import numpy as np
    from PIL import Image
    print("PyMuPDF and OpenCV available!")
except ImportError as e:
    print("Missing library:", e)
    sys.exit(1)

my_scans = r"F:\My Scans"
dest_folder = r"F:\1983"
os.makedirs(dest_folder, exist_ok=True)

pdf_files = [f for f in os.listdir(my_scans) if "bariloche" in f.lower() and f.endswith(".pdf")]
print(f"Encontrados {len(pdf_files)} PDFs de Bariloche.")
for pf in pdf_files:
    print(" -", pf)
