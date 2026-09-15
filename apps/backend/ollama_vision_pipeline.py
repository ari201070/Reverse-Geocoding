import os
import json
import base64
from typing import Dict, Any, Optional

try:
    import ollama
except ImportError:
    ollama = None

VLM_TIMEOUT_S = int(os.environ.get("VLM_TIMEOUT_S", "45"))
DEFAULT_VLM_MODEL = os.environ.get("DEFAULT_VLM_MODEL", "moondream")

def _extract_json(raw_text: str) -> dict:
    if not raw_text:
        return {}
    try:
        # Try direct JSON load
        return json.loads(raw_text.strip())
    except Exception:
        pass
    
    try:
        start = raw_text.find('{')
        end = raw_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            clean = raw_text[start:end + 1]
            return json.loads(clean)
    except Exception:
        pass
        
    return {}

def extract_semantic_fingerprint(image_bytes: bytes, model: str = DEFAULT_VLM_MODEL) -> Dict[str, Any]:
    """
    Extracts semantic fingerprint (OCR text, location name, micro-fisonomía visual elements)
    from image bytes using local Ollama (moondream or llama3.2).
    100% local, zero external paid APIs.
    """
    if not ollama:
        return {"error": "ollama package not installed", "success": False}
        
    try:
        client = ollama.Client(timeout=VLM_TIMEOUT_S)
        prompt = (
            "Analyze this photo for Reverse Geocoding and Semantic Fingerprinting. "
            "Extract any visible text, business names, street signs, landmarks, or distinctive visual elements "
            "(furniture, interior/exterior style, signage). "
            "Respond ONLY with a valid JSON object in this exact format: "
            "{"
            "  \"location_name\": \"Detected place name or UNKNOWN\","
            "  \"ocr_text\": \"All readable text found in the image\","
            "  \"visual_labels\": [\"label1\", \"label2\"],"
            "  \"landmark_hint\": \"Famous monument or building if recognized\","
            "  \"confidence\": 0.85"
            "}"
        )
        
        res = client.chat(
            model=model,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_bytes],
            }],
            options={'temperature': 0.0, 'top_p': 0.1},
        )
        
        content = res.get('message', {}).get('content', '{}')
        data = _extract_json(content)
        data['success'] = True
        data['model_used'] = model
        return data
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model_used": model,
            "location_name": "UNKNOWN",
            "ocr_text": "",
            "visual_labels": []
        }
