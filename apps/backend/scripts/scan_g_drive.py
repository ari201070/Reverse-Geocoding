"""
scan_g_drive.py - Ingesta robusta de fotos Bosnia + vouchers Italia desde G:\
Uso:
  python scripts/scan_g_drive.py           # Solo fotos nuevas
  python scripts/scan_g_drive.py --remap   # Re-procesa fotos UNMAPPED sin GPS
  python scripts/scan_g_drive.py --diag    # Solo diagnostico, sin insertar
Requiere: server.py en localhost:8000 (para VLM OCR)
"""
import io, sys, os, json, time, sqlite3, hashlib, re, tempfile, zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    print("[!] Pillow no instalado. pip install Pillow"); sys.exit(1)
try:
    from geopy.geocoders import Nominatim
except ImportError:
    print("[!] geopy no instalado. pip install geopy"); sys.exit(1)
try:
    import httpx
except ImportError:
    print("[!] httpx no instalado. pip install httpx"); sys.exit(1)
try:
    from pypdf import PdfReader
except ImportError:
    print("[!] pypdf no instalado. pip install pypdf"); sys.exit(1)

# =========================
# Config
# =========================
DB_PATH = r"F:\photo_catalog.db"
BOOKINGS_PATH = Path(__file__).resolve().parent.parent / "src" / "data" / "initialBookings.json"
BOSNIA_DIR = Path(r"G:\האחסון שלי\טיול לבוסניה והרצגובינה")
ITALY_DIR = Path(r"G:\האחסון שלי\גברים רעבים באיטליה")
API_BASE = "http://localhost:8000"
VLM_DELAY = 4.5
NOMINATIM_DELAY = 1.0

BOSNIA_TRIP_START = "2023-04-29"
BOSNIA_TRIP_END = "2023-05-06"

BOSNIA_RESILIENT_MAP = [
    {"kw": ["ostrozac", "stari grad"], "name": "Stari Grad Ostrozac", "loc": "Ostrozac, Bosnia and Herzegovina", "lat": 44.9042, "lng": 15.9421},
    {"kw": ["martin brod", "una"], "name": "NP Una / Martin Brod", "loc": "Martin Brod, Bosnia and Herzegovina", "lat": 44.4925, "lng": 16.1425},
    {"kw": ["bihac"], "name": "Bihac", "loc": "Bihac, Bosnia and Herzegovina", "lat": 44.8167, "lng": 15.8708},
    {"kw": ["stari most", "mostar"], "name": "Stari Most / Mostar", "loc": "Mostar, Bosnia and Herzegovina", "lat": 43.3438, "lng": 17.8078},
    {"kw": ["tunnel of hope", "tunel spasa", "sarajevo"], "name": "Sarajevo / Tunnel of Hope", "loc": "Sarajevo, Bosnia and Herzegovina", "lat": 43.8563, "lng": 18.4131},
    {"kw": ["radimlja"], "name": "Necropolis de Radimlja", "loc": "Stolac, Bosnia and Herzegovina", "lat": 43.0847, "lng": 17.9221},
    {"kw": ["kravica"], "name": "Cascadas de Kravica", "loc": "Kravica, Bosnia and Herzegovina", "lat": 43.1581, "lng": 17.6083},
]
# Official Bosnia itinerary landmarks (extended)
BOSNIA_LANDMARKS = BOSNIA_RESILIENT_MAP + [
    {"kw": ["tito", "bunker"], "name": "Tito's Bunker", "loc": "Konjic, Bosnia and Herzegovina", "lat": 43.6511, "lng": 17.9622},
    {"kw": ["radimlja", "nekropola", "stecci", "stec"], "name": "Radimlja Necropolis (Stecci)", "loc": "Stolac, Bosnia and Herzegovina", "lat": 43.0848, "lng": 17.9225},
    {"kw": ["stari most", "mostar bridge", "old bridge"], "name": "Stari Most (Old Bridge)", "loc": "Mostar, Bosnia and Herzegovina", "lat": 43.3373, "lng": 17.8150},
    {"kw": ["kravica", "waterfall", "waterfalls"], "name": "Kravice Waterfalls", "loc": "Kravice, Bosnia and Herzegovina", "lat": 43.1581, "lng": 17.6083},
    {"kw": ["vijecnica", "city hall", "sarajevo city"], "name": "Sarajevo City Hall (Vijecnica)", "loc": "Sarajevo, Bosnia and Herzegovina", "lat": 43.8589, "lng": 18.4350},
    {"kw": ["tunnel of hope", "tunel spasa", "tunnel"], "name": "Tunnel of Hope (Tunel Spasa)", "loc": "Sarajevo, Bosnia and Herzegovina", "lat": 43.8247, "lng": 18.3314},
    {"kw": ["vrelo bosne", "bosna springs"], "name": "Vrelo Bosne (Bosna Springs)", "loc": "Sarajevo, Bosnia and Herzegovina", "lat": 43.8182, "lng": 18.2694},
    {"kw": ["blagaj", "tekija", "dervish"], "name": "Blagaj Tekija (Dervish House)", "loc": "Blagaj, Bosnia and Herzegovina", "lat": 43.2570, "lng": 17.8914},
    {"kw": ["livno", "horses", "cincar", "wild horse"], "name": "Livno Wild Horses (Cincar)", "loc": "Livno, Bosnia and Herzegovina", "lat": 43.8242, "lng": 17.0051},
    {"kw": ["jajce", "fortress", "pliva"], "name": "Jajce Fortress & Pliva Waterfall", "loc": "Jajce, Bosnia and Herzegovina", "lat": 44.3414, "lng": 17.2681},
    {"kw": ["national park una", "una national", "park una", "una river", "rijeka una", "strbacki", "buk"], "name": "Una National Park", "loc": "Bihac, Bosnia and Herzegovina", "lat": 44.4925, "lng": 16.1425},
    {"kw": ["mostar"], "name": "Mostar (city center)", "loc": "Mostar, Bosnia and Herzegovina", "lat": 43.3373, "lng": 17.8150},
    {"kw": ["sarajevo"], "name": "Sarajevo (city)", "loc": "Sarajevo, Bosnia and Herzegovina", "lat": 43.8563, "lng": 18.4131},
    {"kw": ["jablanica"], "name": "Jablanica", "loc": "Jablanica, Bosnia and Herzegovina", "lat": 43.6606, "lng": 17.7617},
    {"kw": ["pocitelj"], "name": "Pocitelj (historic village)", "loc": "Pocitelj, Bosnia and Herzegovina", "lat": 43.1333, "lng": 17.7333},
    {"kw": ["medugorje", "medjugorje"], "name": "Medugorje (pilgrimage site)", "loc": "Medugorje, Bosnia and Herzegovina", "lat": 43.1917, "lng": 17.6750},
    {"kw": ["konjic"], "name": "Konjic (Old Bridge)", "loc": "Konjic, Bosnia and Herzegovina", "lat": 43.6511, "lng": 17.9622},
    {"kw": ["trebinje"], "name": "Trebinje", "loc": "Trebinje, Bosnia and Herzegovina", "lat": 42.7116, "lng": 18.3458},
    {"kw": ["ostrozac", "ostro\u017eac"], "name": "Castillo de Ostrozac", "loc": "Ostrozac, Bosnia and Herzegovina", "lat": 44.9042, "lng": 15.9421},
    {"kw": ["martin brod"], "name": "Martin Brod (Una Canyon)", "loc": "Martin Brod, Bosnia and Herzegovina", "lat": 44.4925, "lng": 16.1425},
    {"kw": ["bihac", "biha\u0107"], "name": "Bihac (city)", "loc": "Bihac, Bosnia and Herzegovina", "lat": 44.8122, "lng": 15.8681},
]

ITALY_HOTEL_PATTERNS = [
    {"pat": r"(?:B&B|Bed\s*&\s*Breakfast)\s+Marb[o\u00f2]", "id": "hotel-marbo-florence-2023", "title": "B&B Marb\u00f2 Florence (Hotel)", "cat": "hotel", "sup": "Booking.com", "loc": "Via Alamanni 25, 50125 Firenze, Italia", "lat": 43.7781, "lng": 11.2454, "city": "Firenze"},
    {"pat": r"Hotel\s+Soperga", "id": "hotel-soperga-milan-2023", "title": "Hotel Soperga Milano (Hotel)", "cat": "hotel", "sup": "Booking.com", "loc": "Via Soperga 24, 20127 Milano, Italia", "lat": 45.4884, "lng": 9.2101, "city": "Milano"},
    {"pat": r"Sun\s*Moon", "id": "hotel-sun-moon-roma-2023", "title": "Sun Moon Rome (Hotel)", "cat": "hotel", "sup": "Booking.com", "loc": "Via Dei Mille 41A, 00185 Roma, Italia", "lat": 41.9029, "lng": 12.5056, "city": "Roma"},
    {"pat": r"(?:Palma\s+Residence|Palma\s+Hotel)", "id": "hotel-palma-roma-2023", "title": "Palma Residence Roma (Hotel)", "cat": "hotel", "sup": "", "loc": "Roma, Italia", "lat": 41.9029, "lng": 12.5056, "city": "Roma"},
]
ITALY_ACTIVITY_PATTERNS = [
    {"pat": r"(?:Capilla\s+Sixtina|Museos?\s+Vaticanos?|Vatican)", "id": "tour-vaticano-2023", "title": "Visita Guiada Museos Vaticanos y Capilla Sixtina", "cat": "actividad", "loc": "Musei Vaticanos, Citta del Vaticano", "lat": 41.9065, "lng": 12.4536},
    {"pat": r"(?:Colosseum|Coliseo|Colosseo)", "id": "tour-coliseo-2023", "title": "Colosseum, Roman Forum, and Palatine Hill Tour", "cat": "actividad", "loc": "Piazza del Colosseo, Roma, Italia", "lat": 41.8902, "lng": 12.4922},
    {"pat": r"(?:Museo\s+Leonardo\s+da\s+Vinci|Da\s+Vinci)", "id": "museo-da-vinci-2023", "title": "Museo Leonardo da Vinci", "cat": "actividad", "loc": "Via Melzi d'Eril 20, Milano, Italia", "lat": 45.4884, "lng": 9.2101},
    {"pat": r"Pantheon", "id": "pantheon-roma-2023", "title": "Pantheon Roma", "cat": "actividad", "loc": "Piazza della Rotonda, Roma, Italia", "lat": 41.8986, "lng": 12.4768},
]
ITALY_FLIGHT_PATTERNS = [
    {"pat": r"(?:Ryanair|FR\d{3,4})", "id": "vuelo-tlv-fco-2023", "title": "Vuelo TLV - FCO (Ryanair)", "cat": "vuelo"},
    {"pat": r"(?:Israir|6H\s*\d{3,4})", "id": "vuelo-tlv-fco-israir-2023", "title": "Vuelo TLV - FCO (Israir)", "cat": "vuelo"},
]
ITALY_TRANSPORT_PATTERNS = [
    {"pat": r"(?:Terravision|bus.*(?:Fiumicino|Ciampino|FCO|CIA))", "id": "bus-terravision-2023", "title": "Bus Traslado Aeropuerto (Terravision)", "cat": "transporte"},
    {"pat": r"(?:Tren.*(?:Alta\s+Velocidad|Italo|Trenitalia|Frecce)|Roma.*Firenze|Firenze.*Roma)", "id": "tren-roma-firenze-2023", "title": "Tren Alta Velocidad Italo (Roma - Florencia)", "cat": "transporte"},
]

# =========================
# Utilities
# =========================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def extract_exif_pillow(file_path):
    try:
        img = Image.open(file_path)
        exif = img._getexif()
        if not exif:
            return {}
        decoded = {TAGS.get(k, k): v for k, v in exif.items()}
        gps_info = decoded.get("GPSInfo")
        lat = lng = None
        if gps_info:
            gps_decoded = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}
            def to_deg(v):
                try:
                    d, m, s = v
                    return float(d[0])/float(d[1]) + float(m[0])/float(m[1])/60 + float(s[0])/float(s[1])/3600
                except: return None
            lat_val = to_deg(gps_decoded.get("GPSLatitude"))
            lng_val = to_deg(gps_decoded.get("GPSLongitude"))
            if lat_val is not None and lng_val is not None:
                if gps_decoded.get("GPSLatitudeRef") == "S": lat_val = -lat_val
                if gps_decoded.get("GPSLongitudeRef") == "W": lng_val = -lng_val
                lat, lng = lat_val, lng_val
        date_taken = decoded.get("DateTimeOriginal") or decoded.get("DateTime")
        if date_taken:
            if isinstance(date_taken, bytes): date_taken = date_taken.decode(errors="ignore")
            date_taken = str(date_taken).replace(":", "-", 2) if ":" in str(date_taken) else str(date_taken)
        return {"lat": lat, "lng": lng, "date_taken": date_taken}
    except: return {}

def create_thumbnail(file_path, max_size=1024):
    try:
        img = Image.open(file_path)
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.convert("RGB").save(tmp.name, "JPEG", quality=85)
        return tmp.name
    except: return str(file_path)

def sanitize_string(s: str) -> str:
    if not isinstance(s, str): return ""
    s = s.replace("\x00", "").replace(";", "").replace("--", "").replace("/*", "").replace("`", "")
    s = s.replace("'", "''")
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return s

def normalize_text(s: str) -> str:
    import unicodedata
    if not s: return ""
    s = sanitize_string(s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("&amp;", " ").replace("&lt;", " ").replace("&gt;", " ").replace("&quot;", " ").replace("''", " ")
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    s = re.sub(r"\s+", " ", s).strip()
    return s

def fuzzy_score(a: str, b: str) -> int:
    if not a or not b: return 0
    ta, tb = set(normalize_text(a).split()), set(normalize_text(b).split())
    if not ta or not tb: return 0
    inter = ta & tb
    return round(2 * len(inter) / (len(ta) + len(tb)) * 100)

def call_vlm_ocr(file_path):
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "image/jpeg")}
            r = httpx.post(f"{API_BASE}/api/extract-voucher", files=files, timeout=30)
            if r.status_code == 200:
                j = r.json()
                voucher_data = j.get("voucher", {}) if isinstance(j, dict) else {}
                extracted_text = voucher_data.get("location_name", "") or voucher_data.get("raw_output", "")
                if not extracted_text and isinstance(j, dict):
                    for k in ("raw_output", "text", "output", "response", "result"):
                        if j.get(k):
                            extracted_text = j[k]
                            break
                        if voucher_data.get(k):
                            extracted_text = voucher_data[k]
                            break
                j["_extracted_text"] = extracted_text
                return j
    except Exception as e:
        print(f" [VLM ERR:{e}]", end="", flush=True)
    return None

def check_vlm_server():
    """Single circuit-breaker check: probe localhost:8000 with 1s timeout."""
    try:
        r = httpx.get(f"{API_BASE}/", timeout=1.0)
        return r.status_code < 500
    except Exception:
        return False

def match_landmark(vlm_text):
    if not vlm_text: return None
    t = normalize_text(vlm_text)
    for lm in BOSNIA_LANDMARKS:
        for kw in lm["kw"]:
            if normalize_text(kw) in t:
                return lm["name"], lm["loc"], lm["lat"], lm["lng"]
    return None

def extract_date_from_filename(filename):
    m = re.search(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", filename)
    if m:
        y, mo, d, h, mi, s = m.groups()
        return f"{y}-{mo}-{d} {h}:{mi}:{s}"
    m = re.search(r"(\d{4})(\d{2})(\d{2})", filename)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{mo}-{d}"
    return None

def geocode_nominatim(name):
    if not name: return None, None
    try:
        geo = Nominatim(user_agent="scan-g-drive-8000")
        loc = geo.geocode(name, timeout=5)
        if loc: return round(loc.latitude, 6), round(loc.longitude, 6)
    except: pass
    return None, None

def city_from_coords(lat, lng):
    if not lat or not lng: return None, None, None
    regions = [
        (43.8, 43.95, 18.3, 18.55, "Sarajevo", "Sarajevo"),
        (43.25, 43.45, 17.7, 17.95, "Mostar", "Herzegovina-Neretva"),
        (43.55, 43.75, 17.8, 18.15, "Konjic", "Herzegovina-Neretva"),
        (43.2, 43.4, 17.55, 18.05, "Blagaj", "Herzegovina-Neretva"),
        (42.95, 43.25, 17.75, 18.05, "Stolac", "Herzegovina-Neretva"),
        (44.25, 44.45, 17.15, 17.35, "Jajce", "Central Bosnia"),
        (44.75, 44.95, 15.75, 15.95, "Bihac", "Una-Sana"),
        (43.75, 43.95, 16.95, 17.15, "Livno", "Canton 10"),
        (44.85, 45.0, 15.85, 16.0, "Ostrozac", "Una-Sana"),
        (44.4, 44.6, 16.05, 16.25, "Martin Brod", "Una-Sana"),
    ]
    for latmin, latmax, lngmin, lngmax, city, prov in regions:
        if latmin <= lat <= latmax and lngmin <= lng <= lngmax:
            return city, prov, "Bosnia and Herzegovina"
    return None, None, "Bosnia and Herzegovina"

def insert_photo(conn, pd):
    try:
        conn.execute("""
            INSERT OR REPLACE INTO photos (
                original_path, final_path, filename, file_hash, file_size,
                date_taken, year, month_folder, lat, lng, location_name,
                is_duplicate, merged_from, created_at, location_source,
                inherited_from_voucher_id, city, province, country,
                h3_index, date_source, trip_name
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            pd["original_path"], pd["final_path"], pd["filename"], pd["file_hash"],
            pd["file_size"], pd["date_taken"], pd["year"], pd["month_folder"],
            pd["lat"], pd["lng"], pd["location_name"], 0, None,
            datetime.now().isoformat(), pd["location_source"], None,
            pd["city"], pd["province"], pd["country"], None,
            pd["date_source"], pd["trip_name"],
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f" [DB ERR:{e}]", end="", flush=True)
        return False

# =========================
# Bosnia Scanning
# =========================

def scan_bosnia(remap=False):
    print("\n" + "=" * 60)
    print(f"BOSNIA 2023 - {'REMAP unmapped' if remap else 'Scan nuevo'}")
    print("=" * 60)

    if not BOSNIA_DIR.exists():
        print(f"[!] Directorio no encontrado: {BOSNIA_DIR}")
        return 0, 0, []

    conn = get_db()
    img_ext = (".jpg", ".jpeg", ".png", ".heic")
    files = [f for f in os.listdir(BOSNIA_DIR) if f.lower().endswith(img_ext)]
    print(f"  Imagenes en directorio: {len(files)}")

    # Pre-flight: try reading first file
    if files:
        test_fp = BOSNIA_DIR / files[0]
        try:
            with open(test_fp, "rb") as fh:
                fh.read(10)
            print(f"  Acceso a archivos: OK")
        except PermissionError:
            print(f"  [!] ERROR: No se puede leer archivos de G: drive")
            print(f"  >>> Los archivos estan en modo Cloud-only de Google Drive")
            print(f"  >>> Haz clic derecho sobre la carpeta en Google Drive")
            print(f"  >>> y selecciona 'Acceso sin conexion > Mantener en este dispositivo'")
            conn.close()
            return 0, 0, []
        except Exception as e:
            print(f"  [!] ERROR leyendo archivos: {e}")
            conn.close()
            return 0, 0, []

    # Circuit breaker: single probe to VLM server
    vlm_active = check_vlm_server()
    if vlm_active:
        print(f"  Servidor VLM (puerto 8000): ACTIVO")
    else:
        print(f"  [INFO] Servidor VLM local (puerto 8000) no responde. Se desactiva la inferencia de IA para este lote para evitar retardos de conexion.")

    exif_count = 0
    vlm_count = 0
    inserted = 0
    skipped = 0
    report = []

    for idx, filename in enumerate(files, 1):
        file_path = str(BOSNIA_DIR / filename)
        file_path_norm = file_path.replace("\\", "/")

        # Check if already in DB
        if not remap:
            existing = conn.execute(
                "SELECT id, location_source FROM photos WHERE original_path = ?",
                (file_path_norm,)
            ).fetchone()
            if existing:
                skipped += 1
                continue

        # If remap, only process UNMAPPED ones
        if remap:
            existing = conn.execute(
                "SELECT id, location_source, lat FROM photos WHERE original_path = ?",
                (file_path_norm,)
            ).fetchone()
            if existing and existing[1] != "UNMAPPED" and existing[2] is not None:
                skipped += 1
                continue

        print(f"  [{idx}/{len(files)}] {filename}...", end=" ", flush=True)

        # Extract EXIF
        exif = extract_exif_pillow(file_path)
        date_taken = exif.get("date_taken")
        lat = exif.get("lat")
        lng = exif.get("lng")
        location_source = None
        location_name = None
        ocr_text = "-"

        if lat is not None and lng is not None:
            location_source = "EXIF_GPS"
            exif_count += 1
            print(f"EXIF_GPS ({lat:.4f},{lng:.4f})")
        elif vlm_active:
            # VLM OCR for ALL images without GPS (server is up)
            print("VLM...", end=" ", flush=True)
            tmp_thumb = None
            try:
                tmp_thumb = create_thumbnail(file_path, max_size=1024)
                vlm_result = call_vlm_ocr(tmp_thumb)
                time.sleep(VLM_DELAY)

                vlm_text = ""
                vlm_lat = vlm_lng = None
                vlm_source = None
                if vlm_result:
                    voucher_data = vlm_result.get("voucher", {}) if isinstance(vlm_result.get("voucher"), dict) else {}
                    extracted_text = voucher_data.get("location_name", "") or voucher_data.get("raw_output", "")
                    if not extracted_text:
                        extracted_text = vlm_result.get("_extracted_text", "") or voucher_data.get("text", "") or vlm_result.get("text", "") or ""
                    vlm_text = extracted_text
                    vlm_lat = voucher_data.get("lat") if isinstance(voucher_data, dict) else None
                    vlm_lng = voucher_data.get("lng") if isinstance(voucher_data, dict) else None
                    vlm_source = voucher_data.get("location_source") if isinstance(voucher_data, dict) else None
                    if vlm_lat is None:
                        vlm_lat = vlm_result.get("lat")
                        vlm_lng = vlm_result.get("lng")
                        vlm_source = vlm_result.get("location_source")

                if vlm_text: ocr_text = vlm_text[:120]

                if vlm_lat is not None and vlm_lng is not None:
                    lat, lng = vlm_lat, vlm_lng
                    location_source = vlm_source or "VLM_OCR"
                    location_name = vlm_text
                    vlm_count += 1
                    print(f"VLM '{vlm_text[:40]}' ({lat:.4f},{lng:.4f})")
                else:
                    landmark = match_landmark(vlm_text)
                    if landmark:
                        lm_name, lm_loc, lm_lat, lm_lng = landmark
                        lat, lng = lm_lat, lm_lng
                        location_source = "VLM_OCR_MATCH"
                        location_name = lm_name
                        vlm_count += 1
                        print(f"LANDMARK '{lm_name}' ({lat:.4f},{lng:.4f})")
                    else:
                        location_source = "UNMAPPED"
                        print(f"UNMAPPED '{vlm_text[:50]}'")
            finally:
                if tmp_thumb and tmp_thumb != file_path:
                    try: os.unlink(tmp_thumb)
                    except: pass
        else:
            # VLM offline — use filename regex + landmark heuristics only
            location_source = "UNMAPPED"
            print(f"NO_VLM (date-only)")

        # Date from filename fallback
        if not date_taken:
            date_taken = extract_date_from_filename(filename)

        # City from coordinates
        city, province, country = city_from_coords(lat, lng)

        # Year/month
        year = month_folder = None
        if date_taken:
            try:
                parts = date_taken.split(" ")[0].split("-")
                year = int(parts[0])
                month_folder = int(parts[1])
            except: pass

        pd = {
            "original_path": file_path_norm,
            "final_path": file_path_norm,
            "filename": filename,
            "file_hash": file_hash(file_path),
            "file_size": os.path.getsize(file_path),
            "date_taken": date_taken,
            "year": year,
            "month_folder": month_folder,
            "lat": round(lat, 6) if lat else None,
            "lng": round(lng, 6) if lng else None,
            "location_name": location_name,
            "location_source": location_source,
            "city": city,
            "province": province,
            "country": country or "Bosnia and Herzegovina",
            "date_source": "EXIF" if exif.get("date_taken") else "FILENAME",
            "trip_name": "bosnia-2023",
        }

        if insert_photo(conn, pd):
            inserted += 1

        report.append({
            "archivo": filename,
            "gps_exif": "Si" if exif.get("lat") else "No",
            "texto_ocr": ocr_text,
            "origen": location_source or "UNMAPPED",
            "coordenadas": f"{lat:.6f},{lng:.6f}" if lat else "-",
        })

    conn.close()
    print(f"\n  --- Resultado Bosnia ---")
    print(f"  Directorio: {len(files)} archivos")
    print(f"  Omitidos (ya en DB): {skipped}")
    print(f"  Procesados: {inserted}")
    print(f"  GPS EXIF: {exif_count}")
    print(f"  VLM OCR: {vlm_count}")
    return inserted, vlm_count, report

# =========================
# Italy Scanning
# =========================

def normalize_italy_date(s):
    sep = "/" if "/" in s else "."
    parts = s.split(sep)
    if len(parts) == 3:
        d, m, y = parts
        if len(y) == 2: y = "20" + y
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    return None

def parse_italy_pdf(fp, fn):
    try:
        reader = PdfReader(fp)
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
    except: return []
    vouchers = []
    for pat in ITALY_HOTEL_PATTERNS:
        if re.search(pat["pat"], text, re.IGNORECASE):
            price = None
            pm = re.search(r"\u20ac\s*([\d.,]+)", text)
            if pm:
                try: price = float(pm.group(1).replace(".","").replace(",","."))
                except: pass
            dates = re.findall(r"(\d{1,2}[/.]\d{1,2}[/.]\d{2,4})", text)
            sd = normalize_italy_date(dates[0]) if dates else None
            ed = normalize_italy_date(dates[-1]) if len(dates) >= 2 else sd
            gm = re.search(r"N\s+0*(\d+)\s*°.*?([\d.]+)\s*,\s*E\s+0*(\d+)\s*°.*?([\d.]+)", text, re.I|re.S)
            lat, lng = pat["lat"], pat["lng"]
            if gm:
                try: lat = int(gm.group(1)) + float(gm.group(2))/60; lng = int(gm.group(3)) + float(gm.group(4))/60
                except: pass
            vouchers.append({"id": pat["id"], "fileName": f"{pat['title']} ({fn})", "isTravelDocument": True, "category": pat["cat"], "supplier": pat.get("sup",""), "title": pat["title"], "startDate": sd or "2023-10-02", "endDate": ed or "2023-10-12", "confirmationNumber": "", "location": pat["loc"], "coordinates": {"lat": round(lat,6), "lng": round(lng,6)}, "price": price, "currency": "EUR", "details": f"Extraido de {fn}", "mimeType": "application/pdf", "tripId": "italia-2023", "trip_id": "italia-2023", "city": pat.get("city",""), "amount": price, "start_date": sd or "2023-10-02", "latitude": round(lat,6), "longitude": round(lng,6), "summary": pat["title"], "category_normalized": pat["cat"]})
    for pat in ITALY_ACTIVITY_PATTERNS:
        if re.search(pat["pat"], text, re.IGNORECASE):
            price = None
            pm = re.search(r"\u20ac\s*([\d.,]+)", text)
            if pm:
                try: price = float(pm.group(1).replace(".","").replace(",","."))
                except: pass
            vouchers.append({"id": pat["id"], "fileName": f"{pat['title']} ({fn})", "isTravelDocument": True, "category": pat["cat"], "supplier": "", "title": pat["title"], "startDate": "2023-10-02", "endDate": "2023-10-12", "confirmationNumber": "", "location": pat["loc"], "coordinates": {"lat": pat["lat"], "lng": pat["lng"]}, "price": price, "currency": "EUR", "details": f"Extraido de {fn}", "mimeType": "application/pdf", "tripId": "italia-2023", "trip_id": "italia-2023", "city": "", "amount": price, "start_date": "2023-10-02", "latitude": pat["lat"], "longitude": pat["lng"], "summary": pat["title"], "category_normalized": pat["cat"]})
    for pat in ITALY_FLIGHT_PATTERNS:
        if re.search(pat["pat"], text, re.IGNORECASE):
            vouchers.append({"id": pat["id"], "fileName": f"{pat['title']} ({fn})", "isTravelDocument": True, "category": pat["cat"], "supplier": "", "title": pat["title"], "startDate": "2023-10-02", "endDate": "2023-10-02", "confirmationNumber": "", "location": "TLV -> FCO", "coordinates": {"lat": 32.0055, "lng": 34.8854}, "price": None, "currency": "EUR", "details": f"Extraido de {fn}", "mimeType": "application/pdf", "tripId": "italia-2023", "trip_id": "italia-2023", "city": "", "amount": None, "start_date": "2023-10-02", "latitude": 32.0055, "longitude": 34.8854, "summary": pat["title"], "category_normalized": pat["cat"]})
    for pat in ITALY_TRANSPORT_PATTERNS:
        if re.search(pat["pat"], text, re.IGNORECASE):
            price = None
            pm = re.search(r"\u20ac\s*([\d.,]+)", text)
            if pm:
                try: price = float(pm.group(1).replace(".","").replace(",","."))
                except: pass
            vouchers.append({"id": pat["id"], "fileName": f"{pat['title']} ({fn})", "isTravelDocument": True, "category": pat["cat"], "supplier": "", "title": pat["title"], "startDate": "2023-10-02", "endDate": "2023-10-12", "confirmationNumber": "", "location": "", "coordinates": {"lat": 41.9029, "lng": 12.5056}, "price": price, "currency": "EUR", "details": f"Extraido de {fn}", "mimeType": "application/pdf", "tripId": "italia-2023", "trip_id": "italia-2023", "city": "", "amount": price, "start_date": "2023-10-02", "latitude": 41.9029, "longitude": 12.5056, "summary": pat["title"], "category_normalized": pat["cat"]})
    return vouchers

def scan_italy():
    print("\n" + "=" * 60)
    print("ITALIA 2023 - Voucher Scanning (PDF)")
    print("=" * 60)
    if not ITALY_DIR.exists():
        print(f"[!] Directorio no encontrado: {ITALY_DIR}")
        return 0
    existing_bookings = []
    existing_ids = set()
    if BOOKINGS_PATH.exists():
        with open(BOOKINGS_PATH, "r", encoding="utf-8") as f:
            existing_bookings = json.load(f)
            existing_ids = {b.get("id") for b in existing_bookings}
    pdfs = [f for f in os.listdir(ITALY_DIR) if f.lower().endswith(".pdf")]
    print(f"  PDFs: {len(pdfs)}")
    new_vouchers = []
    for fn in pdfs:
        fp = str(ITALY_DIR / fn)
        vouchers = parse_italy_pdf(fp, fn)
        for v in vouchers:
            if v["id"] not in existing_ids:
                new_vouchers.append(v)
                existing_ids.add(v["id"])
                print(f"    -> {v['id']}: {v['title']}")
    xlsx = ITALY_DIR / "\u05ea\u05db\u05e0\u05d9\u05ea \u05e0\u05e1\u05d9\u05e2\u05d4 \u05e9\u05dc \u05ea\u05d5\u05e6\u05e2\u05d4 \u05dc\u05d0\u05d9\u05d8\u05dc\u05d9\u05d4.xlsx"
    if xlsx.exists():
        try:
            z = zipfile.ZipFile(xlsx)
            tree = ET.parse(z.open("xl/sharedStrings.xml"))
            ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            strings = [t.text or "" for t in tree.findall(".//ns:t", ns)]
            full = " ".join(strings).lower()
            if "palma" in full and "hotel-palma-roma-2023-itinerary" not in existing_ids:
                new_vouchers.append({"id": "hotel-palma-roma-2023-itinerary", "fileName": "Palma Residence Roma (Itinerario)", "isTravelDocument": True, "category": "hotel", "supplier": "", "title": "Palma Residence Roma (Hotel)", "startDate": "2023-10-02", "endDate": "2023-10-04", "confirmationNumber": "", "location": "Roma, Italia", "coordinates": {"lat": 41.9029, "lng": 12.5056}, "price": 354.72, "currency": "EUR", "details": "Extraido de itinerario XLSX", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "tripId": "italia-2023", "trip_id": "italia-2023", "city": "Roma", "amount": 354.72, "start_date": "2023-10-02", "latitude": 41.9029, "longitude": 12.5056, "summary": "Palma Residence Roma", "category_normalized": "hotel"})
                print(f"    -> hotel-palma-roma-2023-itinerary: Palma Residence Roma")
        except: pass
    if new_vouchers:
        all_b = existing_bookings + new_vouchers
        with open(BOOKINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(all_b, f, indent=2, ensure_ascii=False)
        print(f"\n  +{len(new_vouchers)} vouchers guardados en {BOOKINGS_PATH.name}")
    else:
        print("\n  Sin nuevos vouchers")
    return len(new_vouchers)

def generate_report(report):
    rp = Path(__file__).resolve().parent.parent / "reporte_escaneo_bosnia.md"
    total = len(report)
    exif = sum(1 for r in report if r["gps_exif"] == "Si")
    vlm = sum(1 for r in report if r["origen"] in ("VLM_OCR", "VLM_OCR_MATCH"))
    lm = sum(1 for r in report if r["origen"] == "VLM_LANDMARK_MATCH")
    unm = sum(1 for r in report if r["origen"] == "UNMAPPED")
    lines = [
        "# Reporte de Escaneo - Bosnia 2023",
        "", f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Directorio:** `{BOSNIA_DIR}`", f"**Total imagenes:** {total}", "",
        "## Resumen", "",
        "| Metrica | Valor |", "|---|---|",
        f"| Total imagenes | {total} |",
        f"| Con GPS EXIF nativo | {exif} |",
        f"| VLM OCR (coords directas) | {vlm} |",
        f"| Landmark Match | {lm} |",
        f"| Sin mapeo (UNMAPPED) | {unm} |",
        f"| **Total geolocalizadas** | **{exif+vlm+lm}** |", "",
        "## Detalle", "",
        "| Archivo | GPS | Texto OCR | Origen | Coordenadas |",
        "|---|---|---|---|---|",
    ]
    for r in report:
        t = r["texto_ocr"].replace("|","\\|")[:100] if r["texto_ocr"] else "-"
        lines.append(f"| {r['archivo']} | {r['gps_exif']} | {t} | {r['origen']} | {r['coordenadas']} |")
    lines += ["", "---", f"*Generado por `scripts/scan_g_drive.py`*"]
    with open(rp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  Reporte: {rp}")

# =========================
# Main
# =========================

def main():
    args = sys.argv[1:]
    remap = "--remap" in args
    diag_only = "--diag" in args

    print("=" * 60)
    print("G: DRIVE SCAN - Bosnia + Italia")
    print(f"Modo: {'DIAGNOSTICO' if diag_only else 'REMAP' if remap else 'SCAN'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Pre-flight
    print(f"\n[Pre-flight]")
    print(f"  DB: {DB_PATH} ({'OK' if os.path.exists(DB_PATH) else 'NOT FOUND'})")
    print(f"  Bosnia: {BOSNIA_DIR} ({'OK' if BOSNIA_DIR.exists() else 'NOT FOUND'})")
    print(f"  Italy: {ITALY_DIR} ({'OK' if ITALY_DIR.exists() else 'NOT FOUND'})")
    print(f"  Bookings: {BOOKINGS_PATH} ({'OK' if BOOKINGS_PATH.exists() else 'NOT FOUND'})")

    if diag_only:
        print("\n  Modo diagnostico — sin insertar")
        if BOSNIA_DIR.exists():
            imgs = [f for f in os.listdir(BOSNIA_DIR) if f.lower().endswith(('.jpg','.jpeg','.png','.heic'))]
            print(f"  Bosnia images: {len(imgs)}")
            if imgs:
                fp = str(BOSNIA_DIR / imgs[0])
                try:
                    with open(fp, "rb") as fh: fh.read(10)
                    print(f"  First file readable: YES")
                except Exception as e:
                    print(f"  First file readable: NO ({e})")
        return

    b_ins, b_vlm, report = scan_bosnia(remap=remap)
    if report: generate_report(report)
    i_new = scan_italy()

    print("\n" + "=" * 60)
    print("REPORTE FINAL")
    print("=" * 60)
    print(f"  Bosnia: +{b_ins} insertadas, {b_vlm} VLM OCR")
    print(f"  Italia: +{i_new} vouchers nuevos")
    print("=" * 60)
    print("Done.")

if __name__ == "__main__":
    main()
