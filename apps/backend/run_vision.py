import subprocess, json, base64, os, sys

img_path = r"C:\Users\flier\AppData\Local\Temp\opencode\photo_095800.jpg"

# 1. Pytesseract OCR
print("=== PYTESSERACT OCR ===")
try:
    import pytesseract
    from PIL import Image
    text = pytesseract.image_to_string(Image.open(img_path), lang='eng')
    print(text[:2000])
except Exception as e:
    print(f"Tesseract error: {e}")

# 2. Ollama vision - llava
print("\n=== OLLAMA LLAVA-13B VISION ===")
try:
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    payload = {
        "model": "llava:13b",
        "prompt": "Describe this image in detail. What building is this? What architectural style? List any visible text, signs, inscriptions, or distinctive features. Output ONLY a JSON object with keys: building, style, location, visible_text, features",
        "images": [img_b64],
        "stream": False
    }
    
    import urllib.request
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", 
                                  data=json.dumps(payload).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
        print(result.get("response", "no response")[:3000])
except Exception as e:
    print(f"llava error: {e}")

# 3. Ollama vision - moondream
print("\n=== OLLAMA MOONDREAM VISION ===")
try:
    payload = {
        "model": "moondream",
        "prompt": "What building is shown in this image? Describe the architecture, any visible text, and identify the location. Respond with JSON: {building, style, location, text_visible}",
        "images": [img_b64],
        "stream": False
    }
    
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", 
                                  data=json.dumps(payload).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
        print(result.get("response", "no response")[:3000])
except Exception as e:
    print(f"moondream error: {e}")
