import sys
import requests
import base64
import json
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def test_ollama_vision(image_path, model="qwen2.5-vl:7b"):
    try:
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {
            "model": model,
            "prompt": "Analyze this photo and identify the landmark. Return JSON with: landmark (name), location (city, country), confidence (0-1)",
            "images": [image_base64],
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '')
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Exception: {str(e)}"

test_images = [
    r'F:\2023\10-Octubre\2023-10-04 10.36.26_IMG_20231004_103626.jpg',
    r'F:\2023\10-Octubre\2023-10-04 10.36.29_IMG_20231004_103629.jpg',
]

print("=== TEST VISION OLLAMA ===")
for img_path in test_images:
    print(f"\nProbando: {os.path.basename(img_path)}")
    if os.path.exists(img_path):
        result = test_ollama_vision(img_path)
        print(f"Resultado: {result[:500]}")
    else:
        print("Archivo no encontrado")
