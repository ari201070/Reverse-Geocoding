from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import ollama
import json
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

app = FastAPI()

geolocator = Nominatim(user_agent="travel_booking_document_hub_local_v1")

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
    
    prompt = (
        "Extract ONLY these two fields from this travel document or receipt (ticket, invoice, hotel booking, flight boarding pass, restaurant receipt):\n"
        "1. location_name: The SPECIFIC establishment, restaurant, hotel, store, or service provider name (e.g. 'Pizzería Guerrín' or 'Café Delirac' - NOT just the generic city name).\n"
        "2. datetime: The date and time of the event/transaction in format YYYY-MM-DD HH:MM (extract from the printed receipt text).\n"
        "Return strictly a raw JSON object with these two keys, nothing else."
    )
    
    response = ollama.chat(
        model='qwen2.5vl:7b',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [contents]
        }]
    )
    
    raw_text = response['message']['content']
    clean_json = raw_text[raw_text.find('{'):raw_text.rfind('}')+1]
    
    try:
        data = json.loads(clean_json)
        location_name = data.get("location_name", "")
        datetime_str = data.get("datetime", "")
    except Exception:
        location_name = ""
        datetime_str = ""
        print(f"[AVISO] No se pudo parsear JSON. Respuesta cruda: {raw_text}")

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
