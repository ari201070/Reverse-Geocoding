"""
Microservicio Python: Punto de entrada HTTP para el orquestador de Node.js.

Endpoints definidos:
  POST /analyze-exif      → Extracción de metadatos EXIF/GPS de una imagen
  POST /reconcile-name    → Comparación semántica OCR vs nombre oficial (RapidFuzz)
  GET  /health            → Estado del servicio
"""
from flask import Flask, request, jsonify
import exifread
import io
from rapidfuzz import fuzz
import math

app = Flask(__name__)

# --- Utilidades ---

def round_coord(val: float) -> float:
    """Protocolo de privacidad: redondeo a 4 decimales (~11m)."""
    return round(float(val), 4)

def decimal_from_dms(dms, ref):
    """Convierte DMS EXIF a decimal firmado."""
    d, m, s = [float(x.num) / float(x.den) for x in dms.values]
    dd = d + m / 60 + s / 3600
    return -dd if ref in ('S', 'W') else dd


# --- Endpoints ---

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "reverse-geocoding-py"}), 200


@app.route('/analyze-exif', methods=['POST'])
def analyze_exif():
    """
    Recibe un archivo de imagen y devuelve coordenadas GPS, timestamp,
    y precisión horizontal (GPSHPositioningError).
    Espera multipart/form-data con campo 'image'.
    """
    if 'image' not in request.files:
        return jsonify({"error": "Missing 'image' field"}), 400

    image_bytes = request.files['image'].read()
    tags = exifread.process_file(io.BytesIO(image_bytes), details=False)

    result = {}

    try:
        lat = decimal_from_dms(tags['GPS GPSLatitude'], str(tags['GPS GPSLatitudeRef']))
        lng = decimal_from_dms(tags['GPS GPSLongitude'], str(tags['GPS GPSLongitudeRef']))
        result['lat'] = round_coord(lat)
        result['lng'] = round_coord(lng)
    except KeyError:
        result['lat'] = None
        result['lng'] = None

    result['timestamp'] = str(tags.get('EXIF DateTimeOriginal', ''))
    result['gps_accuracy'] = str(tags.get('GPS GPSHPositioningError', ''))
    
    # Extract Image Direction (v3.2)
    dir_tag = tags.get('GPS GPSImgDirection')
    if dir_tag:
        try:
            val = float(dir_tag.values[0].num) / float(dir_tag.values[0].den)
            result['direction'] = round(val, 2)
        except:
            result['direction'] = None
    else:
        result['direction'] = None

    return jsonify(result), 200


@app.route('/reconcile-name', methods=['POST'])
def reconcile_name():
    """
    Compara un fragmento de texto OCR contra un nombre oficial usando RapidFuzz.
    Body JSON: { "ocr_text": "...", "official_name": "..." }
    Devuelve: { "score": 0..100, "match": bool }
    """
    body = request.get_json(force=True)
    ocr_text = body.get('ocr_text', '')
    official_name = body.get('official_name', '')

    if not ocr_text or not official_name:
        return jsonify({"error": "Missing ocr_text or official_name"}), 400

    score = fuzz.token_set_ratio(ocr_text, official_name)
    return jsonify({"score": score, "match": score >= 75}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
