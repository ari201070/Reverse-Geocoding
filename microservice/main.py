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
import datetime
import pytz
from astral import Observer
from astral.sun import azimuth

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


# --- Mapeo de Direcciones de Sombra a Grados ---
DIRECTION_MAPPING = {
    "north": 0, "n": 0,
    "north-east": 45, "ne": 45, "northeast": 45,
    "east": 90, "e": 90,
    "south-east": 135, "se": 135, "southeast": 135,
    "south": 180, "s": 180,
    "south-west": 225, "sw": 225, "southwest": 225,
    "west": 270, "w": 270,
    "north-west": 315, "nw": 315, "northwest": 315,
}

def parse_datetime(dt_str: str) -> datetime.datetime:
    """Parsea una fecha EXIF o ISO y la hace aware de UTC."""
    s = dt_str.strip()
    if len(s) >= 19 and s[4] == ':' and s[7] == ':':
        s = s[:4] + '-' + s[5:7] + '-' + s[8:]
        
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            dt = datetime.datetime.strptime(s, fmt)
            return dt.replace(tzinfo=pytz.UTC)
        except ValueError:
            continue
    return datetime.datetime.now(pytz.UTC)

def get_shadow_angle_from_dir(dir_val) -> float:
    """Resuelve la dirección de sombra (en texto o ángulo directo) a grados."""
    if dir_val is None:
        return None
    try:
        return float(dir_val)
    except (ValueError, TypeError):
        s = str(dir_val).strip().lower()
        return DIRECTION_MAPPING.get(s, None)


@app.route('/calculate-consensus', methods=['POST'])
def calculate_consensus():
    """
    Calcula el puntaje de consenso ponderado de Antigravity 2.0 y aplica el veto físico solar.
    Body JSON: {
        "lat": float,
        "lng": float,
        "timestamp": str,
        "ocr_score": float,  -- 0.0 a 1.0 (de RapidFuzz / 100)
        "landmark_score": float,  -- 0.0 a 1.0
        "observed_shadow_direction": str/float
    }
    """
    body = request.get_json(force=True)
    
    lat = body.get('lat')
    lng = body.get('lng')
    timestamp_str = body.get('timestamp', '')
    ocr_score = float(body.get('ocr_score', 0.0))
    landmark_score = float(body.get('landmark_score', 0.0))
    shadow_dir = body.get('observed_shadow_direction')

    if lat is not None:
        lat = round_coord(lat)
    if lng is not None:
        lng = round_coord(lng)

    solar_divergence = None
    solar_sync_score = 0.0
    evidence_parts = []

    if lat is not None and lng is not None and timestamp_str and shadow_dir is not None:
        observed_angle = get_shadow_angle_from_dir(shadow_dir)
        if observed_angle is not None:
            try:
                dt_utc = parse_datetime(timestamp_str)
                obs = Observer(latitude=lat, longitude=lng, elevation=0)
                sun_az = azimuth(obs, dt_utc)
                theoretical_shadow = (sun_az + 180) % 360
                
                diff = abs(observed_angle - theoretical_shadow)
                solar_divergence = min(diff, 360 - diff)
                
                if solar_divergence <= 15.0:
                    solar_sync_score = 1.0
                    evidence_parts.append(f"Sincronización Solar exitosa (Divergencia: {round(solar_divergence, 2)}°)")
                else:
                    solar_sync_score = 0.0
                    evidence_parts.append(f"Falla Sincronización Solar (Divergencia: {round(solar_divergence, 2)}° > 15°)")
            except Exception as e:
                evidence_parts.append(f"Error en Sincronización Solar: {str(e)}")
        else:
            evidence_parts.append(f"No se pudo mapear la dirección de sombra: {shadow_dir}")
    else:
        evidence_parts.append("Datos solares incompletos")

    if solar_divergence is not None and solar_divergence > 15.0:
        return jsonify({
            "confidence_score": 0.0,
            "review_status": "REJECTED",
            "solar_divergence": round(solar_divergence, 2),
            "evidence": "VETO FÍSICO: La divergencia solar observada (" + str(round(solar_divergence, 2)) + "°) supera el límite crítico de 15°."
        }), 200

    WEIGHTS = {"ocr": 0.40, "solar": 0.30, "landmarks": 0.30}
    total_score = (
        (ocr_score * WEIGHTS["ocr"]) +
        (solar_sync_score * WEIGHTS["solar"]) +
        (landmark_score * WEIGHTS["landmarks"])
    )
    
    if total_score > 0.75:
        status = "RECONSTRUCTED"
    elif total_score > 0.40:
        status = "PENDING_REVIEW"
    else:
        status = "REJECTED"

    evidence_parts.append(f"OCR: {round(ocr_score * 100, 1)}%, Hitos: {round(landmark_score * 100, 1)}%")
    evidence = " | ".join(evidence_parts)

    return jsonify({
        "confidence_score": round(total_score, 2),
        "review_status": status,
        "solar_divergence": round(solar_divergence, 2) if solar_divergence is not None else None,
        "evidence": evidence
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
