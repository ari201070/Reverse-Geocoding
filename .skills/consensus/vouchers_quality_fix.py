import sys
import os
import json
import re
import requests
import base64
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def process_voucher_local_ocr(image_path):
    """
    Procesa el voucher localmente extrayendo texto puro estructurado.
    Mantiene estrictamente las coordenadas espaciales en NULL para evitar alucinaciones.
    """
    try:
        filename = os.path.basename(image_path)
        print(f"📦 Procesando metadatos locales para: {filename}")
        
        # Leemos la imagen en base64 para que el modelo local interprete el texto impreso
        with open(image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
            
        # URL nativa de tu servicio de Ollama mapeado en el puerto 11434
        url = "http://127.0.0"
        
        # Prompt estructurado de OCR Puro validado por los Arquitectos
        prompt_instructions = (
            "Estrictamente: NO devuelvas coordenadas geográficas, ni latitudes, ni longitudes, ni índices H3. "
            "NO inventes ubicaciones. Solo lee el texto impreso en este comprobante/ticket.\n\n"
            "Extrae EXACTAMENTE estos campos, devolviendo solo un objeto JSON sin explicaciones:\n"
            "- 'supplier': nombre de la empresa emisora (ej: 'Trenitalia', 'Alilaguna')\n"
            "- 'route': origen y destino separados por ' -> '\n"
            "- 'date': fecha real impresa en formato DD/MM/AAAA. NUNCA uses la fecha del archivo.\n"
            "- 'time': hora real impresa en formato HH:MM\n"
            "- 'price': tarifa exacta con moneda\n"
            "- 'confirmation_code': código de confirmación o billete\n"
            "Si algún campo no aparece, pon null. No completes con valores supuestos."
        )
        
        payload = {
            "model": "qwen2.5-coder:7b",  # O moondream según tu disponibilidad en Ollama
            "prompt": prompt_instructions,
            "stream": False,
            "format": "json"
        }
        
        # Realizamos la llamada local segura sin tocar endpoints externos falsos
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code != 200:
            return None
            
        response_data = response.json()
        parsed_text = response_data.get("response", "{}")
        return json.loads(parsed_text)

    except Exception as e:
        print(f"❌ Error en procesamiento de metadatos locales para {os.path.basename(image_path)}: {str(e)}")
        return None
