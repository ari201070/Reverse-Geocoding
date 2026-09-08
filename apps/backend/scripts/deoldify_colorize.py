import sys
import os

# Change to DeOldify directory for model loading
deoldify_dir = r'C:\Users\flier\AppData\Local\Temp\opencode\DeOldify'
os.chdir(deoldify_dir)
sys.path.insert(0, deoldify_dir)

from pathlib import Path
from deoldify import device
from deoldify.device_id import DeviceId
from deoldify.visualize import get_image_colorizer
import torch

# Set device to CPU
device.set(DeviceId.CPU)
torch.backends.cudnn.benchmark = False

def colorize_photo(input_path, output_path, render_factor=35):
    """Colorize a photo using DeOldify"""
    print(f"Colorizing: {input_path}")
    
    colorizer = get_image_colorizer(artistic=True)
    
    # Colorize the image
    result_path = colorizer.plot_transformed_image(
        path=input_path,
        render_factor=render_factor,
        compare=False,
        watermarked=False
    )
    
    # Move the result to the desired output path
    if result_path and os.path.exists(result_path):
        import shutil
        shutil.move(str(result_path), output_path)
        print(f"  Saved: {output_path}")
        return True
    else:
        print(f"  Failed to colorize")
        return False

# Process the photos
base = r"F:\SinFecha_Desconocido\1983\11-Noviembre"

photos = [
    (f"{base}\\2010-11-14 18.12.09_Scan_Pic0001.jpg", f"{base}\\familia_fuente_deoldify.jpg"),
    (f"{base}\\2010-11-14 18.57.04_Casamiento Papa y Mama.jpg", f"{base}\\casamiento_deoldify.jpg"),
]

for input_path, output_path in photos:
    if os.path.exists(input_path):
        colorize_photo(input_path, output_path)
    else:
        print(f"File not found: {input_path}")

print("\nDone!")
