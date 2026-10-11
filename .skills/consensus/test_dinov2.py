import sys
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModel
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

print("📦 [DINOv2] Iniciando descarga e instanciación local del modelo desde HuggingFace...")

# Descarga local del modelo base (se guarda en la caché local de tu usuario, ej. ~/.cache)
processor = AutoProcessor.from_pretrained("facebook/dinov2-base")
model = AutoModel.from_pretrained("facebook/dinov2-base")

print("✅ [ÉXITO] Modelo DINOv2 descargado y cargado en memoria correctamente.")

# Prueba rápida con una función de extracción de prueba
def verificar_arquitectura():
    print(f"🖥️  Dispositivo de ejecución seleccionado: {'CUDA (GPU)' if torch.cuda.is_available() else 'CPU'}")
    print("📐 Parámetros del modelo listos para mapas de características densas.")

verificar_arquitectura()
