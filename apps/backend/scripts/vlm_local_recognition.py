import os
import sys
import io
import json
import sqlite3
import glob
from datetime import datetime

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

try:
    import ollama
except ImportError:
    print("[!] pip install ollama")
    sys.exit(1)

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

# Translate DB month names to disk folder names with prefixes
MONTH_TRANSLATION = {
    r"\Enero\\": r"\01-Enero\\",
    r"\Febrero\\": r"\02-Febrero\\",
    r"\Marzo\\": r"\03-Marzo\\",
    r"\Abril\\": r"\04-Abril\\",
    r"\Mayo\\": r"\05-Mayo\\",
    r"\Junio\\": r"\06-Junio\\",
    r"\Julio\\": r"\07-Julio\\",
    r"\Agosto\\": r"\08-Agosto\\",
    r"\Septiembre\\": r"\09-Septiembre\\",
    r"\Octubre\\": r"\10-Octubre\\",
    r"\Noviembre\\": r"\11-Noviembre\\",
    r"\Diciembre\\": r"\12-Diciembre\\",
    r"/Enero/": r"/01-Enero/",
    r"/Febrero/": r"/02-Febrero/",
    r"/Marzo/": r"/03-Marzo/",
    r"/Abril/": r"/04-Abril/",
    r"/Mayo/": r"/05-Mayo/",
    r"/Junio/": r"/06-Junio/",
    r"/Julio/": r"/07-Julio/",
    r"/Agosto/": r"/08-Agosto/",
    r"/Septiembre/": r"/09-Septiembre/",
    r"/Octubre/": r"/10-Octubre/",
    r"/Noviembre/": r"/11-Noviembre/",
    r"/Diciembre/": r"/12-Diciembre/"
}

def translate_path(path, filename=None):
    if not path:
        return path
    path_clean = path.replace("\\", "/")
    
    # Flat October 2025 rule
    if "Octubre" in path_clean and filename:
        return os.path.normpath(f"F:/2025/10-Octubre/{filename}")
        
    for old, new in MONTH_TRANSLATION.items():
        old_clean = old.replace("\\\\", "\\").replace("\\", "/").strip("/")
        new_clean = new.replace("\\\\", "\\").replace("\\", "/").strip("/")
        if f"/{old_clean}/" in path_clean:
            path_clean = path_clean.replace(f"/{old_clean}/", f"/{new_clean}/")
            break
    return os.path.normpath(path_clean)

def analyze_image_with_moondream(image_path):
    """
    Sends the image bytes to local Ollama using moondream model to extract semantic info.
    """
    if not os.path.exists(image_path):
        return {"error": f"File not found on disk: {image_path}", "success": False}
        
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        client = ollama.Client()
        
        # Turn 1: Short Description
        response1 = client.chat(
            model='moondream',
            messages=[{
                'role': 'user',
                'content': "Describe what is shown in this photo in one short sentence.",
                'images': [image_bytes]
            }],
            options={'temperature': 0.0}
        )
        desc = response1.get('message', {}).get('content', '').strip()
        
        # Turn 2: Precise Place Name
        response2 = client.chat(
            model='moondream',
            messages=[{
                'role': 'user',
                'content': "Name the specific business, building, street, monument, or natural attraction shown. Respond with the name only in 1-4 words. If unknown or general, respond 'UNKNOWN'.",
                'images': [image_bytes]
            }],
            options={'temperature': 0.0}
        )
        place = response2.get('message', {}).get('content', '').strip().strip('.').strip('"').strip("'")
        
        # Clean up place name from potential model prefixes
        if place.lower().startswith("it's ") or place.lower().startswith("it is "):
            place = place[place.lower().find("it") + 5:]
            
        return {
            "success": True,
            "description": desc,
            "location_name": place,
            "ocr_text": desc,
            "landmark_hint": place if place != "UNKNOWN" else "None",
            "visual_labels": ["photo"]
        }
    except Exception as e:
        return {"error": str(e), "success": False}

def main():
    print("=== INICIANDO GEOLOCALIZACIÓN Y ENRIQUECIMIENTO VISUAL LOCAL VLM (MOONDREAM) ===")
    
    # Check if DB exists
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    # We will process a batch of 5 photos from F:\2025\10-Octubre to demonstrate moondream,
    # and also look for 5 unmapped photos in F:\2025 to see if we can resolve them.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # A. Demo Batch from October 2025 (requested by user)
        # We find files in the DB corresponding to Octubre 2025.
        print("\n--- Procesando Lote de F:\\2025\\10-Octubre (Enriquecimiento de LandMarks) ---")
        cursor = conn.execute("""
            SELECT id, file_path, filename, lat, lng, location_name 
            FROM photos 
            WHERE file_path LIKE '%2025%Octubre%' 
              AND (filename LIKE '202510%' OR filename LIKE '2025-10%')
              AND (filename LIKE '%.jpg' OR filename LIKE '%.jpeg' OR filename LIKE '%.png'
                   OR filename LIKE '%.JPG' OR filename LIKE '%.JPEG' OR filename LIKE '%.PNG')
            LIMIT 50
        """)
        oct_rows = cursor.fetchall()
        
        valid_oct_row = None
        for r in oct_rows:
            disk_path = translate_path(r['file_path'], r['filename'])
            if os.path.exists(disk_path):
                valid_oct_row = r
                break
                
        if not valid_oct_row:
            print("No se encontraron archivos físicos de Octubre 2025 en el disco F:.")
        else:
            r = valid_oct_row
            db_path = r['file_path']
            disk_path = translate_path(db_path, r['filename'])
            print(f"\nID: {r['id']} | Archivo: {r['filename']}")
            print(f"  Ruta DB:   {db_path}")
            print(f"  Ruta Disco: {disk_path}")
            print(f"  Coordenadas actuales: ({r['lat']}, {r['lng']}) | {r['location_name'] or 'Sin nombre'}")
            
            print("  [VLM] Analizando con moondream...")
            analysis = analyze_image_with_moondream(disk_path)
            if analysis.get('success'):
                print(f"    - Lugar Detectado: {analysis.get('location_name')}")
                print(f"    - OCR Text:        {analysis.get('ocr_text')}")
                print(f"    - Landmark Hint:   {analysis.get('landmark_hint')}")
                print(f"    - Visual Labels:   {analysis.get('visual_labels')}")
                
                # Enrich location_name if moondream found a landmark/sight and DB location is empty
                detected_loc = analysis.get('landmark_hint') or analysis.get('location_name')
                if detected_loc and detected_loc != "UNKNOWN" and detected_loc != "None":
                    current_loc = r['location_name']
                    new_loc = f"{detected_loc}" if not current_loc else f"{current_loc} ({detected_loc})"
                    conn.execute("""
                        UPDATE photos 
                        SET location_name = ?, location_address = ?, confidence_score = 0.88
                        WHERE id = ?
                    """, (new_loc, analysis.get('ocr_text'), r['id']))
                    conn.commit()
                    print(f"    [DB] Registro actualizado con éxito: {new_loc}")
            else:
                print(f"    [Error VLM] {analysis.get('error')}")
                    
        # B. Unmapped Batch from 2025 (SIN_GEO)
        print("\n--- Procesando Lote de fotos 2025 SIN_GEO (Geolocalización por VLM) ---")
        cursor = conn.execute("""
            SELECT id, file_path, filename 
            FROM photos 
            WHERE lat IS NULL AND date_taken LIKE '2025%'
              AND (filename LIKE '%.jpg' OR filename LIKE '%.jpeg' OR filename LIKE '%.png'
                   OR filename LIKE '%.JPG' OR filename LIKE '%.JPEG' OR filename LIKE '%.PNG')
            LIMIT 50
        """)
        unmapped_rows = cursor.fetchall()
        
        valid_unmapped_row = None
        for r in unmapped_rows:
            disk_path = translate_path(r['file_path'], r['filename'])
            if os.path.exists(disk_path):
                valid_unmapped_row = r
                break
                
        if not valid_unmapped_row:
            print("No se encontraron fotos físicas de 2025 sin geolocalizar registradas.")
        else:
            r = valid_unmapped_row
            db_path = r['file_path']
            disk_path = translate_path(db_path, r['filename'])
            print(f"\nID: {r['id']} | Archivo: {r['filename']}")
            print(f"  Ruta DB:   {db_path}")
            print(f"  Ruta Disco: {disk_path}")
            
            print("  [VLM] Analizando con moondream...")
            analysis = analyze_image_with_moondream(disk_path)
            if analysis.get('success'):
                print(f"    - Lugar Detectado: {analysis.get('location_name')}")
                print(f"    - OCR Text:        {analysis.get('ocr_text')}")
                print(f"    - Landmark Hint:   {analysis.get('landmark_hint')}")
                
                # Try to geocode if name found
                detected_loc = analysis.get('landmark_hint') or analysis.get('location_name')
                if detected_loc and detected_loc != "UNKNOWN" and detected_loc != "None":
                    # Try simple fallback coordinates matching city/landmarks
                    from space_temporal_inheritance import _fallback_coords
                    fb = _fallback_coords(detected_loc)
                    if fb:
                        lat, lng = fb
                        conn.execute("""
                            UPDATE photos 
                            SET lat = ?, lng = ?, latitude = ?, longitude = ?,
                                location_name = ?, location_source = 'VISION_LANDMARK',
                                confidence_score = 0.85
                            WHERE id = ?
                        """, (lat, lng, lat, lng, detected_loc, r['id']))
                        conn.commit()
                        print(f"    [DB] ¡Ubicación resuelta! Asignadas coordenadas de fallback ({lat}, {lng})")
                    else:
                        print("    [Geocoding] No se encontraron coordenadas de fallback para el término.")
            else:
                print(f"    [Error VLM] {analysis.get('error')}")
                    
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un fallo en el proceso VLM: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
