from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import sqlite3
import urllib.parse
import tempfile
import re
from datetime import datetime
from typing import Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = FastAPI(title="Photo Catalog - Hybrid 3-Layer Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

DB_PATH = r"F:\photo_catalog.db"
BOOKINGS_PATH = os.path.join(os.path.dirname(__file__), "src", "data", "initialBookings.json")

# =========================
# Capa 3: Mapa Fallback Urbano (centros urbanos) - garantiza pin aunque sin direccion exacta
# =========================
CITY_FALLBACK = {
    "buenos aires": (-34.6037, -58.3816),
    "rosario": (-32.9442, -60.6505),
    "bariloche": (-41.1335, -71.3103),
    "mendoza": (-32.8908, -68.8272),
    "salta": (-24.1858, -65.2995),
    "jujuy": (-24.1858, -65.2995),
    "iguazu": (-25.5972, -54.5766),
    "ibera": (-28.5433, -57.155),
    "corrientes": (-27.4692, -58.8306),
    "roma": (41.9029, 12.5056),
    "florencia": (43.7781, 11.2454),
    "firenze": (43.7781, 11.2454),
    "milan": (45.4884, 9.2101),
    "milán": (45.4884, 9.2101),
    "sarajevo": (43.8563, 18.4131),
    "mostar": (43.3373, 17.815),
    "konjic": (43.6511, 17.9622),
    "jablanica": (43.6606, 17.7617),
    "blagaj": (43.257, 17.8914),
    "bled": (46.2528, 14.4533),
    "ljubljana": (46.0569, 14.5058),
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _fallback_coords(city: str):
    if not city:
        return None
    k = city.strip().lower()
    for name, coords in CITY_FALLBACK.items():
        if name in k or k in name:
            return coords
    return None

def _load_bookings():
    try:
        with open(BOOKINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _find_voucher_inheritance(photo_dt: Optional[str]):
    if not photo_dt:
        return None
    try:
        dt = datetime.fromisoformat(photo_dt.replace(" ", "T").replace("/", "-"))
        date_only = dt.date().isoformat()
    except Exception:
        try:
            date_only = photo_dt.split(" ")[0].split("T")[0].replace(":", "-").replace("/", "-")
            if len(date_only) != 10:
                return None
        except Exception:
            return None
    for b in _load_bookings():
        s = b.get("startDate") or b.get("start_date") or ""
        e = b.get("endDate") or b.get("end_date") or s
        if not s:
            continue
        s = s.split("T")[0].split(" ")[0]
        e = e.split("T")[0].split(" ")[0]
        if s <= date_only <= e:
            coords = b.get("coordinates")
            if coords and coords.get("lat") is not None:
                return b
            lat = b.get("latitude")
            lng = b.get("longitude")
            if lat is not None and lng is not None:
                return b
    return None

def _extract_exif_pillow(file_path: str):
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        img = Image.open(file_path)
        exif = img._getexif()
        if not exif:
            return {}
        decoded = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            decoded[tag] = value
        gps_info = decoded.get("GPSInfo")
        lat = lng = None
        if gps_info:
            gps_decoded = {}
            for k, v in gps_info.items():
                gps_decoded[GPSTAGS.get(k, k)] = v
            def to_deg(v):
                try:
                    d, m, s = v
                    return float(d[0])/float(d[1]) + float(m[0])/float(m[1])/60 + float(s[0])/float(s[1])/3600
                except Exception:
                    return None
            lat_val = to_deg(gps_decoded.get("GPSLatitude"))
            lng_val = to_deg(gps_decoded.get("GPSLongitude"))
            if lat_val is not None and lng_val is not None:
                if gps_decoded.get("GPSLatitudeRef") == "S":
                    lat_val = -lat_val
                if gps_decoded.get("GPSLongitudeRef") == "W":
                    lng_val = -lng_val
                lat, lng = lat_val, lng_val
        date_taken = decoded.get("DateTimeOriginal") or decoded.get("DateTime")
        result = {}
        if lat is not None and lng is not None:
            result["lat"] = lat
            result["lng"] = lng
            result["location_source"] = "EXIF_GPS"
        if date_taken:
            if isinstance(date_taken, bytes):
                date_taken = date_taken.decode(errors="ignore")
            result["date_taken"] = str(date_taken).replace(":", "-", 2) if ":" in str(date_taken) else str(date_taken)
        return result
    except Exception:
        return {}

def _geocode_nominatim(location_name: str):
    if not location_name:
        return None
    fb = _fallback_coords(location_name)
    if fb:
        # intentar geopy primero, fallback a diccionario
        pass
    try:
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="viaje-argentina-8000")
        loc = geolocator.geocode(location_name, timeout=5)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    return fb


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/")
async def root():
    return {"status": "online", "project": "Photo Catalog", "pipeline": "hybrid-3-layer"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/trips")
async def list_trips():
    conn = get_db()
    rows = conn.execute("""
        SELECT trip_name, COUNT(*) as count
        FROM photos
        WHERE trip_name IS NOT NULL AND trip_name != ''
        GROUP BY trip_name
        ORDER BY trip_name
    """).fetchall()
    conn.close()
    return [{"trip_name": r["trip_name"], "count": r["count"]} for r in rows]


@app.get("/api/photos")
async def get_photos(
    trip_name: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    conn = get_db()
    conditions = []
    params = []
    if trip_name:
        conditions.append("trip_name = ?")
        params.append(trip_name)
    if city:
        conditions.append("city = ?")
        params.append(city)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    total = conn.execute(f"SELECT COUNT(*) FROM photos {where}", params).fetchone()[0]
    sql = f"""
        SELECT id, original_path, final_path, filename,
               lat, lng, date_taken, location_source,
               trip_name, city, province, country
        FROM photos
        {where}
        ORDER BY date_taken ASC
        LIMIT ? OFFSET ?
    """
    rows = conn.execute(sql, params + [limit, offset]).fetchall()
    conn.close()
    photos = []
    for r in rows:
        final_path = r["final_path"] or ""
        thumb_path = ""
        if final_path:
            d = os.path.dirname(final_path)
            b = os.path.basename(final_path)
            thumb_path = os.path.join(d, "_thumbs", f"thumb_{b}").replace("\\", "/")
        photos.append({
            "id": r["id"],
            "original_path": (r["original_path"] or "").replace("\\", "/"),
            "final_path": final_path.replace("\\", "/"),
            "thumb_path": thumb_path,
            "filename": r["filename"],
            "latitude": r["lat"],
            "longitude": r["lng"],
            "datetime_original": r["date_taken"],
            "location_source": r["location_source"],
            "trip_name": r["trip_name"],
            "city": r["city"],
            "province": r["province"],
            "country": r["country"],
        })
    return JSONResponse({"total": total, "limit": limit, "offset": offset, "photos": photos})


@app.get("/api/media")
async def serve_media(path: str = Query(..., description="Ruta fisica del archivo")):
    clean = path.replace("file:///", "").replace("file://", "")
    clean = urllib.parse.unquote(clean)
    if not os.path.isfile(clean):
        return JSONResponse({"detail": f"Not found: {clean}"}, status_code=404)
    return FileResponse(clean)

# =========================
# Capa 1: EXIF via Pillow - inspeccion directa de metadatos hardware
# =========================
@app.get("/api/exif")
async def get_exif(path: str = Query(..., description="Ruta fisica del archivo")):
    clean = urllib.parse.unquote(path.replace("file:///", "").replace("file://", ""))
    if not os.path.isfile(clean):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    exif = _extract_exif_pillow(clean)
    return JSONResponse(exif)

# =========================
# Capa 2: Geocodificacion libre Nominatim
# =========================
@app.get("/api/geocode")
async def geocode(location_name: str = Query(..., description="Nombre de lugar extraido por VLM")):
    coords = _geocode_nominatim(location_name)
    if not coords:
        return JSONResponse({"detail": f"No coords for {location_name}"}, status_code=404)
    return {"location_name": location_name, "lat": coords[0], "lng": coords[1], "source": "nominatim/fallback"}

@app.get("/api/city-fallback")
async def city_fallback(city: str = Query(...)):
    coords = _fallback_coords(city)
    if not coords:
        return JSONResponse({"detail": "No fallback"}, status_code=404)
    return {"city": city, "lat": coords[0], "lng": coords[1], "source": "CITY_FALLBACK"}

# =========================
# Spatial Cache H3 (SQLite)
# =========================
def _ensure_spatial_cache():
    try:
        conn = get_db()
        conn.execute("""CREATE TABLE IF NOT EXISTS spatial_cache (
            h3_index TEXT PRIMARY KEY, latitude REAL NOT NULL, longitude REAL NOT NULL,
            location_name TEXT, city TEXT, country TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spatial_cache_h3 ON spatial_cache(h3_index)")
        conn.execute("""CREATE TABLE IF NOT EXISTS known_places (
            h3_index TEXT PRIMARY KEY, latitude REAL NOT NULL, longitude REAL NOT NULL,
            location_name TEXT, city TEXT, country TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_known_places_h3 ON known_places(h3_index)")
        conn.commit(); conn.close()
    except Exception: pass
_ensure_spatial_cache()

@app.get("/api/spatial-cache")
async def spatial_cache_get(lat: float = Query(...), lng: float = Query(...)):
    try:
        from h3 import latlng_to_cell
        anon_lat = round(float(lat), 4); anon_lng = round(float(lng), 4)
        h3_index = latlng_to_cell(anon_lat, anon_lng, 9)
    except Exception:
        try:
            import h3 as _h3
            anon_lat = round(float(lat), 4); anon_lng = round(float(lng), 4)
            h3_index = _h3.latLngToCell(anon_lat, anon_lng, 9)
        except Exception as e:
            return JSONResponse({"detail": str(e)}, status_code=500)
    conn = get_db()
    row = conn.execute("SELECT h3_index, latitude, longitude, location_name, city, country FROM spatial_cache WHERE h3_index=? UNION SELECT h3_index, latitude, longitude, location_name, city, country FROM known_places WHERE h3_index=? LIMIT 1", (h3_index, h3_index)).fetchone()
    conn.close()
    if row:
        return {"hit": True, "h3_index": row["h3_index"], "latitude": row["latitude"], "longitude": row["longitude"], "location_name": row["location_name"], "city": row["city"], "country": row["country"], "source": "SPATIAL_CACHE_H3"}
    return {"hit": False, "h3_index": h3_index}

@app.post("/api/spatial-cache")
async def spatial_cache_save(payload: dict):
    try:
        lat = float(payload.get("latitude") or payload.get("lat"))
        lng = float(payload.get("longitude") or payload.get("lng"))
        location_name = payload.get("location_name") or payload.get("name") or ""
        city = payload.get("city"); country = payload.get("country")
        from h3 import latlng_to_cell
        anon_lat = round(lat, 4); anon_lng = round(lng, 4)
        h3_index = latlng_to_cell(anon_lat, anon_lng, 9)
    except Exception:
        try:
            import h3 as _h3
            lat = float(payload.get("latitude") or payload.get("lat"))
            lng = float(payload.get("longitude") or payload.get("lng"))
            location_name = payload.get("location_name") or payload.get("name") or ""
            city = payload.get("city"); country = payload.get("country")
            anon_lat = round(lat, 4); anon_lng = round(lng, 4)
            h3_index = _h3.latLngToCell(anon_lat, anon_lng, 9)
        except Exception as e:
            return JSONResponse({"detail": str(e)}, status_code=400)
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO spatial_cache (h3_index, latitude, longitude, location_name, city, country, created_at) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)", (h3_index, anon_lat, anon_lng, location_name, city, country))
    conn.execute("INSERT OR REPLACE INTO known_places (h3_index, latitude, longitude, location_name, city, country, created_at) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)", (h3_index, anon_lat, anon_lng, location_name, city, country))
    conn.commit(); conn.close()
    return {"status": "saved", "h3_index": h3_index, "latitude": anon_lat, "longitude": anon_lng}

# =========================
# Capa 2: VLM Local moondream + Herencia Espacio-Temporal
# POST /api/extract-voucher - flujo semantico completo
# =========================
@app.post("/api/extract-voucher")
async def extract_voucher(file: UploadFile = File(...), datetime_hint: Optional[str] = None):
    suffix = os.path.splitext(file.filename or "upload.jpg")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        data = await file.read()
        tmp.write(data)
        tmp_path = tmp.name
    try:
        exif = _extract_exif_pillow(tmp_path)
        if exif.get("lat") is not None and exif.get("lng") is not None:
            v = {"location_name": None, "datetime": exif.get("date_taken"), "lat": exif["lat"], "lng": exif["lng"], "location_source": "EXIF_GPS", "voucher_id": None, "geocode_source": "exif"}
            return {"status": "success", "voucher": v, **v}

        location_name = None
        extracted_dt = datetime_hint
        raw_output = ""
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        vlm_prompt = (
            "You are a helpful travel assistant and geographic coordinator. Analyze the provided image, which can be EITHER a travel document (such as a voucher, ticket, booking confirmation, hotel bill, boarding pass, or receipt) OR a photograph of a scenic landmark, tourist spot, monument, building, or street sign.\n\n"
            "1. If it is a travel document (voucher/ticket/receipt):\n"
            "   - Extract the name of the service provider, hotel, airline, transit station, or venue.\n"
            "   - Extract the city, region, or country.\n"
            "   - Extract the date and time of the event.\n"
            "   - Set 'location_name' to this extracted provider/venue name and city (e.g., 'Hotel Concorde, Bariloche').\n\n"
            "2. If it is a scenic photograph, landmark, or street sign:\n"
            "   - Identify any tourist attractions, monuments, castles, waterfalls, historical sites, or visible street signs (e.g., 'Nacionalni park Una', 'Stari Grad Ostrožac', 'Mostar Bridge').\n"
            "   - Set 'location_name' to the official name of the landmark and its town/country (e.g., 'Ostrožac Castle, Cazin, Bosnia').\n\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n  \"location_name\": \"Name of the landmark, hotel, or venue (or null if not identifiable)\",\n"
            "  \"datetime\": \"YYYY-MM-DD HH:MM (extracted date and time, or null if not present/identifiable)\"\n}"
        )
        gemini_done = False
        if gemini_key:
            try:
                import google.generativeai as genai
                import PIL.Image as _PIL
                import io as _io
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                img = _PIL.Image.open(_io.BytesIO(data))
                resp = await model.generate_content_async([vlm_prompt, img])
                txt = getattr(resp, "text", "") or ""
                if not txt and getattr(resp, "candidates", None):
                    try: txt = resp.candidates[0].content.parts[0].text
                    except Exception: pass
                raw_output = txt.strip()[:2000]
                try:
                    j = json.loads(txt.strip().replace("```json","").replace("```","").strip())
                    if isinstance(j, dict):
                        location_name = j.get("location_name") or location_name
                        extracted_dt = j.get("datetime") or j.get("date") or extracted_dt
                        raw_output = txt.strip()[:2000]
                except Exception:
                    pass
                if not location_name:
                    m = re.search(r'"location_name"\s*:\s*"([^"]+)"', txt, re.I)
                    if m: location_name = m.group(1).strip()
                if not location_name:
                    m = re.search(r"location_name\s*[:=]\s*([^\n,]+)", txt, re.I)
                    if m: location_name = m.group(1).strip().strip('"').strip("'")
                if location_name and location_name.lower() in ("null","none","n/a"): location_name=None
                if not location_name and txt.strip():
                    try:
                        tmp_j=json.loads(txt)
                        location_name=tmp_j.get("location_name")
                    except: pass
                m2 = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", txt)
                if m2: extracted_dt = m2.group(1)
                gemini_done = bool(txt.strip())
            except Exception as e:
                raw_output = raw_output or f"Gemini error: {e}"[:500]
        if not gemini_done:
            moondream_url = os.environ.get("MOONDREAM_URL", "http://localhost:11434/api/generate")
            try:
                import httpx
                async with httpx.AsyncClient(timeout=8) as client:
                    r = await client.post(moondream_url, json={"model": "moondream", "prompt": vlm_prompt, "stream": False})
                    if r.status_code == 200:
                        try:
                            j = r.json()
                            txt = j.get("response", "") or j.get("text", "") or r.text or ""
                        except Exception:
                            txt = r.text or ""
                        raw_output = raw_output or txt.strip()[:2000]
                        try:
                            jj=json.loads(txt.strip().replace("```json","").replace("```","").strip())
                            if isinstance(jj, dict) and jj.get("location_name"): location_name=jj.get("location_name")
                        except: pass
                        if not location_name:
                            m = re.search(r'"location_name"\s*:\s*"([^"]+)"', txt, re.I)
                            if m: location_name=m.group(1).strip()
                        if not location_name:
                            m = re.search(r"location_name\s*[:=]\s*([^\n,]+)", txt, re.I)
                            if m: location_name = m.group(1).strip().strip('"').strip("'")
                        if not location_name and txt.strip():
                            location_name = txt.strip().split("\n")[0][:200].strip()
                        m2 = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", txt)
                        if m2: extracted_dt = m2.group(1)
            except Exception:
                pass
        if not raw_output:
            raw_output = location_name or ""

        # Fallback heuristico agnostico: inferir ciudad desde filename
        if not location_name:
            name = (file.filename or "").lower()
            for city in CITY_FALLBACK.keys():
                if city in name:
                    location_name = city.title()
                    break

        # Capa 2b: Geocodificacion libre
        lat = lng = None
        geocode_source = None
        if location_name:
            coords = _geocode_nominatim(location_name)
            if coords:
                lat, lng = coords
                geocode_source = "nominatim"

        # Capa 2c: Herencia espacio-temporal por reservas (si no hay coords pero hay datetime)
        voucher_id = None
        if (lat is None or lng is None) and extracted_dt:
            v = _find_voucher_inheritance(extracted_dt)
            if v:
                coords = v.get("coordinates") or {}
                lat = coords.get("lat") if coords.get("lat") is not None else v.get("latitude")
                lng = coords.get("lng") if coords.get("lng") is not None else v.get("longitude")
                if lat is not None and lng is not None:
                    voucher_id = v.get("id")
                    geocode_source = "voucher_inheritance"

        # Capa 3: Fallback urbano por ciudad
        if (lat is None or lng is None) and location_name:
            fb = _fallback_coords(location_name)
            if fb:
                lat, lng = fb
                geocode_source = "CITY_FALLBACK"

        location_source = "VOUCHER_INHERITANCE" if voucher_id else ("GEOCODED" if lat is not None else None)
        v = {"location_name": location_name, "datetime": extracted_dt, "lat": lat, "lng": lng, "location_source": location_source, "voucher_id": voucher_id, "geocode_source": geocode_source, "raw_output": raw_output}
        return {"status": "success", "voucher": v, **v}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
