from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import ollama
import json
import re
import os
import base64
import urllib.request
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

app = FastAPI()

VLM_TIMEOUT_S = 90
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# Cuota CERO facturación: al agotarse, Gemini se desactiva solo hasta el día/mes siguiente
GEMINI_FREE_DAILY_LIMIT = int(os.environ.get("GEMINI_FREE_DAILY_LIMIT", "200"))
GEMINI_FREE_MONTHLY_LIMIT = int(os.environ.get("GEMINI_FREE_MONTHLY_LIMIT", "3000"))
_QUOTA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gemini_quota.json")


def _quota_exhausted() -> bool:
    try:
        with open(_QUOTA_FILE) as f:
            q = json.load(f)
    except (OSError, ValueError):
        q = {}
    from datetime import date
    today, month = str(date.today()), str(date.today())[:7]
    if q.get("day") != today:
        q = {"day": today, "used_day": 0, "month": month, "used_month": 0}
    elif q.get("month") != month:
        q["month"], q["used_month"] = month, 0
    exhausted = (q["used_day"] >= GEMINI_FREE_DAILY_LIMIT
                 or q["used_month"] >= GEMINI_FREE_MONTHLY_LIMIT)
    if exhausted:
        print(f"[CUOTA] Gemini free agotado (día {q['used_day']}/{GEMINI_FREE_DAILY_LIMIT}, "
              f"mes {q['used_month']}/{GEMINI_FREE_MONTHLY_LIMIT}). Pausa hasta reset.")
    return exhausted


def _quota_consume():
    from datetime import date
    today, month = str(date.today()), str(date.today())[:7]
    try:
        with open(_QUOTA_FILE) as f:
            q = json.load(f)
    except (OSError, ValueError):
        q = {}
    if q.get("day") != today:
        q = {"day": today, "used_day": 0, "month": month, "used_month": 0}
    q["used_day"] += 1
    q["used_month"] += 1
    with open(_QUOTA_FILE, "w") as f:
        json.dump(q, f)

geolocator = Nominatim(user_agent="travel_booking_document_hub_local_v1")

PLACEHOLDERS = {"", "...", "UNMAPPED", "N/A", "YYYY-MM-DD HH:MM"}


def _valid_voucher(location_name: str) -> bool:
    return bool(location_name and location_name.strip() not in PLACEHOLDERS
                and "..." not in location_name)


def _extract_json(raw_text: str) -> dict:
    clean = raw_text[raw_text.find('{'):raw_text.rfind('}') + 1]
    try:
        return json.loads(clean)
    except Exception:
        return {}


def _moondream_extract(image_bytes: bytes) -> dict:
    client = ollama.Client(timeout=VLM_TIMEOUT_S)
    res = client.chat(
        model='moondream',
        messages=[{
            'role': 'user',
            'content': ('Extract the place name and date/time printed on this travel '
                        'document or receipt. Respond ONLY with JSON like '
                        '{"location_name": "Hotel Actual", "datetime": "2025-10-10 13:00"}. '
                        'Use real values from the image. If not visible write "UNMAPPED".'),
            'images': [image_bytes],
        }],
        options={'temperature': 0.0, 'top_p': 0.1},
    )
    return _extract_json(res['message']['content'])


def _gemini_extract(image_bytes: bytes, mime: str = 'image/jpeg') -> dict:
    if not GEMINI_API_KEY or _quota_exhausted():
        return {}
    body = json.dumps({
        "contents": [{
            "parts": [
                {"text": ('Extract ONLY: 1. location_name (specific establishment, hotel, '
                          'airline or venue, never just a city). 2. datetime (YYYY-MM-DD HH:MM). '
                          'Respond ONLY with the JSON object.')},
                {"inline_data": {"mime_type": mime,
                                 "data": base64.b64encode(image_bytes).decode()}},
            ],
        }],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    _quota_consume()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return {}
    return _extract_json(text)


def extract_voucher_vlm(image_bytes: bytes, mime: str = 'image/jpeg') -> tuple:
    try:
        data = _moondream_extract(image_bytes)
        if _valid_voucher(data.get("location_name", "")):
            return data.get("location_name", ""), data.get("datetime", ""), "moondream"
    except Exception as e:
        print(f"[VLM] moondream falló ({e}), escalando a L4...")
    try:
        data = _gemini_extract(image_bytes, mime)
        if _valid_voucher(data.get("location_name", "")):
            return data.get("location_name", ""), data.get("datetime", ""), "gemini-l4"
    except Exception as e:
        print(f"[VLM] Gemini L4 falló: {e}")
    return "", "", "none"

CITY_FALLBACKS = {
    "buenos aires": (-34.5979, -58.3969),
    "bariloche": (-41.1334, -71.3114),
    "san carlos de bariloche": (-41.1334, -71.3114),
    "mendoza": (-32.8894, -68.8458),
    "corrientes": (-27.4678, -58.8344),
    "iguazu": (-25.5991, -54.5736),
    "puerto iguazu": (-25.5991, -54.5736),
    "jujuy": (-24.1857, -65.2994),
    "salta": (-24.7821, -65.4232),
    "tigre": (-34.4250, -58.5796)
}

def clean_location_name(text: str) -> str:
    if not text:
        return ""
    text = text.replace("'", "").replace("`", "")
    text = re.sub(r"[#@*()\[\]{}]+", " ", text)
    return " ".join(text.split())

def geocode_place(location_name: str) -> tuple:
    cleaned_name = clean_location_name(location_name)
    if not cleaned_name:
        return None, None

    print(f"Buscando coordenadas para: '{cleaned_name}'...")
    try:
        location = geolocator.geocode(cleaned_name, timeout=10)
        if location:
            print(f"[NOMINATIM OK] Coordenadas encontradas: {location.latitude}, {location.longitude}")
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        print("[AVISO] Timeout en Nominatim. Usando heuristica de fallbacks...")
    except Exception as e:
        print(f"[AVISO] Error en geocode: {e}. Pasando a fallbacks...")

    lower_name = cleaned_name.lower()
    for city, coords in CITY_FALLBACKS.items():
        if city in lower_name:
            print(f"[FALLBACK CITY MATCH] Asignando coordenadas de: {city.title()} -> {coords}")
            return coords, coords

    return None, None

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/extract-voucher")
async def extract_voucher(file: UploadFile = File(...)):
    contents = await file.read()

    location_name, datetime_str, source = extract_voucher_vlm(contents, file.content_type or 'image/jpeg')
    print(f"[VLM] fuente: {source} lugar: {location_name!r}")

    lat, lng = None, None
    if location_name:
        lat, lng = geocode_place(location_name)

    return {
        "status": "success",
        "voucher": {
            "location_name": location_name,
            "datetime": datetime_str,
            "lat": lat,
            "lng": lng
        }
    }
