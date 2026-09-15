from fastapi import FastAPI, File, UploadFile
import ollama
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

app = FastAPI()
geolocator = Nominatim(user_agent="travel_hub_local")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/extract-voucher")
async def extract_voucher(file: UploadFile = File(...)):
    contents = await file.read()
    
    # Prompt ultra-optimizado para velocidad en CPU
    prompt = (
        "Extract to JSON: location_name, address, category (hotel/flight/car_rental/activity/purchase), "
        "supplier, start_date (YYYY-MM-DD), start_time (HH:MM), amount (numeric), currency, summary (Spanish). "
        "ONLY JSON object."
    )
    
    try:
        response = ollama.chat(
            model='moondream:latest',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [contents]
            }]
        )
        
        raw_text = response['message']['content']
        # Buscar el primer { y el último } para limpiar el output
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            clean_json = raw_text[start_idx:end_idx+1]
            data = json.loads(clean_json)
        else:
            raise ValueError("No valid JSON found in model response")
            
    except Exception as e:
        print(f"Model error: {e}")
        data = {
            "location_name": file.filename, 
            "summary": "Error en procesamiento visual (CPU Timeout)",
            "category": "activity"
        }
        
    # Enrich with Geolocation (FOSS / geopy)
    if data.get("location_name") and data["location_name"] != "Unknown":
        try:
            # Create a prioritized list of search queries
            search_queries = [data["location_name"]]
            if data.get("address"):
                search_queries.insert(0, f"{data['location_name']}, {data['address']}")
                search_queries.append(data["address"]) # Fallback to just city/country
            
            location = None
            for query in search_queries:
                try:
                    location = geolocator.geocode(query, timeout=10)
                    if location: break
                except Exception:
                    continue
            
            if location:
                data["latitude"] = location.latitude
                data["longitude"] = location.longitude
        except Exception as e:
            print(f"Geocoding error: {e}")

    return {"status": "success", "voucher": data}
