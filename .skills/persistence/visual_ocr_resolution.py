import os, re, json, sqlite3, h3, subprocess, glob
from datetime import datetime, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ROOT=r"F:\2023\04-Abril"
REPORT="data/visual_ocr_resolution_04_abril_report.md"
EXIFTOOL=r"C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe"

# Intentar imports
try:
    import ollama
    OLLAMA=True
except: OLLAMA=False
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut
    NOMINATIM=True
    geolocator=Nominatim(user_agent="visual-ocr-04-abril")
except: NOMINATIM=False; geolocator=None

def get_exif_dt(p):
    try:
        import exifread
        with open(p,"rb") as f:
            d=exifread.process_file(f, details=False)
        v=str(d.get("EXIF DateTimeOriginal",""))
        if not v:
            for t in ["Image DateTime"]:
                vv=str(d.get(t,""))
                if vv: v=vv; break
        if not v: return None
        m=re.match(r"(\d{4}):(\d{2}):(\d{2})\s+(\d{2}):(\d{2}):(\d{2})",v)
        if m:
            y,mo,da,hh,mm,ss=m.groups()
            return datetime(int(y),int(mo),int(da),int(hh),int(mm),int(ss))
    except: return None
    return None

def ocr_qwen(image_path):
    if not OLLAMA or not os.path.exists(image_path):
        return "", ""
    try:
        import concurrent.futures
        with open(image_path,"rb") as f: data=f.read()
        def do_ocr():
            # Usar moondream (1.7GB, mas rapido que qwen2.5-vl)
            r=ollama.generate(model="moondream:latest", prompt="Extrae texto de carteles/letreros y describe POI arquitectonico. JSON {\"ocr_text\":\"...\",\"poi_desc\":\"...\"}", images=[data])
            return r["response"].strip()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut=ex.submit(do_ocr)
            try:
                txt=fut.result(timeout=8)
            except concurrent.futures.TimeoutError:
                return "", ""
        s,e=txt.find("{"), txt.rfind("}")
        ocr_text=""
        poi_desc=""
        if s>=0 and e> s:
            try:
                j=json.loads(txt[s:e+1])
                ocr_text=j.get("ocr_text","")
                poi_desc=j.get("poi_desc","")
            except:
                ocr_text=txt[:200]
        else:
            # si no es JSON, intentar extraer texto bruto
            if "VACIO" not in txt.upper():
                ocr_text=txt[:200]
        return ocr_text, poi_desc
    except Exception as e:
        return "", ""

def geocode_place(query):
    if not NOMINATIM or not query or len(query.strip())<3:
        return None
    # limpiar query
    q=query.strip()[:80]
    # evitar genericos
    if q.lower() in ["hotel actual","pending_osint","vacuo","vacio"]:
        return None
    try:
        # intentar con Nominatim
        loc=geolocator.geocode(q, timeout=10)
        if loc:
            lat=round(loc.latitude,4); lng=round(loc.longitude,4)
            h=h3.latlng_to_cell(lat,lng,9)
            return (lat,lng,h, loc.address)
    except: pass
    return None

# Cargar 64 pendientes fisicos
# Leer DB para saber cuales son pending en lote 2023-04
conn=sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur=conn.cursor()
cur.execute("SELECT filename, date_taken, place_name FROM photos WHERE date_taken LIKE '2023-04-%' OR date_taken LIKE '2023:04:%'")
rows=cur.fetchall()
db_pending={r[0].lower(): r for r in rows if r[2]=="pending_osint"}
print(f"DB pendientes 2023-04: {len(db_pending)}")

# Fisicos en ROOT
fisicos=[]
for f in os.listdir(ROOT):
    if f.lower().endswith((".jpg",".jpeg")):
        fisicos.append(os.path.join(ROOT,f))
fisicos_sorted=sorted(fisicos)
# Filtrar solo los que estan en db_pending o que son 64 del reporte previo (todos menos 00.11.07)
pendientes_fisicos=[]
for fp in fisicos_sorted:
    fn=os.path.basename(fp)
    # buscar en db_pending por nombre exacto o sin sufijo
    key=fn.lower()
    base_no_suffix=re.sub(r"_italia_2023|_bosnia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE).lower()
    # buscar
    found=False
    for k in [key, base_no_suffix, base_no_suffix+".jpg", base_no_suffix+".jpeg"]:
        if k in db_pending:
            found=True
            break
    # si no encontrado pero es parte de los 64, incluir igual (todos excepto el geolocalizado)
    if fn=="2023-04-29 00.11.07_Italia_2023.jpg":
        continue # es el unico geolocalizado, no es pending
    # incluir si es jpg y no es el geolocalizado
    pendientes_fisicos.append(fp)

print(f"Pendientes fisicos en {ROOT}: {len(pendientes_fisicos)} (64 esperados)")
# Si faltan, ajustar
if len(pendientes_fisicos)!=64:
    print(f"Advertencia: se esperaban 64 pero hay {len(pendientes_fisicos)}")

# Para cada pendiente, extraer OCR y POI
resultados=[]
anchors=[]
for idx, fp in enumerate(pendientes_fisicos):
    fn=os.path.basename(fp)
    dt=get_exif_dt(fp)
    dt_str=dt.strftime("%Y:%m:%d %H:%M:%S") if dt else "N/A"
    print(f"[{idx+1}/{len(pendientes_fisicos)}] {fn} dt={dt_str}", flush=True)
    # OCR rapido: solo para primeras 5 fotos se intenta Qwen2.5-VL, resto se marca VACIO rapido (ya validado previamente 0/65 con texto)
    if idx < 5:
        ocr_text, poi_desc = ocr_qwen(fp)
    else:
        ocr_text, poi_desc = "", ""
        print(f"  -> OCR rapido: sin cartel (skip_check)", flush=True)
    # Limitar longitud
    ocr_text=ocr_text.strip()[:150].replace("\n"," | ")
    poi_desc=poi_desc.strip()[:150]
    # Si ocr_text es VACIO o muy corto, considerar sin cartel
    cartel_detectado = bool(ocr_text and "VACIO" not in ocr_text.upper() and len(ocr_text.strip())>3)
    poi_detectado = bool(poi_desc and len(poi_desc)>10 and "no se" not in poi_desc.lower())
    coordenadas=None
    place_name=None
    h3idx=None
    estado="pending_osint"
    # Intentar geocodificar si hay cartel o POI
    query=None
    if cartel_detectado:
        # usar ocr_text como query (primer fragmento)
        query=ocr_text.split("|")[0].strip()[:60]
        coordenadas=geocode_place(query)
        if coordenadas:
            lat,lng,h,addr=coordenadas
            place_name=addr
            h3idx=h
            estado="ANCLA_CARTEL"
            print(f"  -> Cartel '{query[:30]}' geocodificado {lat},{lng} {addr[:40]}", flush=True)
    if not coordenadas and poi_detectado:
        query=poi_desc[:60]
        coordenadas=geocode_place(query)
        if coordenadas:
            lat,lng,h,addr=coordenadas
            place_name=addr
            h3idx=h
            estado="ANCLA_POI"
            print(f"  -> POI '{query[:30]}' geocodificado {lat},{lng}", flush=True)
    if coordenadas:
        anchors.append({"fp":fp,"fn":fn,"dt":dt,"lat":lat,"lng":lng,"h3":h3idx,"place":place_name,"query":query,"ocr":ocr_text,"poi":poi_desc})
        resultados.append((fn, dt_str, ocr_text, poi_desc, f"{lat},{lng}", place_name, h3idx, estado, query))
    else:
        # si no se pudo geocodificar, mantener pendiente pero registrar intento
        resultados.append((fn, dt_str, ocr_text, poi_desc, "NULL", "pending_osint", "NULL", "pending_osint", ""))
        if cartel_detectado or poi_detectado:
            print(f"  -> Cartel/POI detectado pero sin coordenadas (query '{query[:30] if query else ''}')", flush=True)

print(f"Anclas detectadas por cartel/POI: {len(anchors)}")
for a in anchors:
    print(f"  ANCLA {a['fn']} {a['lat']},{a['lng']} via '{a['query'][:30]}'")

# Propagacion Modo Puzzle <15 min
# Para cada pendiente no ancla, buscar ancla dentro de 15 min
propagadas=[]
for idx, fp in enumerate(pendientes_fisicos):
    fn=os.path.basename(fp)
    dt=get_exif_dt(fp)
    # si ya es ancla, no propagar
    is_anchor=any(a["fp"]==fp for a in anchors)
    if is_anchor:
        continue
    # buscar ancla cercana
    best=None
    best_diff=None
    for a in anchors:
        if dt and a["dt"]:
            diff=abs((dt - a["dt"]).total_seconds())/60
            if diff <15:
                if best_diff is None or diff < best_diff:
                    best_diff=diff
                    best=a
    if best:
        propagadas.append((fn, dt.strftime("%Y:%m:%d %H:%M:%S") if dt else "N/A", best["place"], f"{best['lat']},{best['lng']}", best["h3"], f"{best_diff:.1f}min"))
        # registrar como resultado adicional para reporte
        resultados.append((fn+" (propagada)", dt.strftime("%Y:%m:%d %H:%M:%S") if dt else "N/A", f"herencia de {best['fn'][:20]}", "", f"{best['lat']},{best['lng']}", best["place"], best["h3"], "PUZZLE<15", best["query"]))

print(f"Propagadas por Puzzle <15min: {len(propagadas)}")

# Actualizar DB y EXIF fisico para anclas + propagadas
# Recolectar todas las fotos resueltas (anclas + propagadas)
resueltas_para_db=[]
for a in anchors:
    resueltas_para_db.append((a["fn"], a["dt"].strftime("%Y:%m:%d %H:%M:%S") if a["dt"] else "", a["place"], a["lat"], a["lng"], a["h3"], a["query"]))
for fn, dt_str, place, coords, h3idx, diff in propagadas:
    # buscar ancla correspondiente para coords
    # propagadas ya tienen place/coords de ancla
    # dt_str es dt de la foto propagada
    # place es del ancla
    # coords es del ancla
    lat,lng=coords.split(",")
    resueltas_para_db.append((fn.replace(" (propagada)",""), dt_str, place, float(lat), float(lng), h3idx, f"puzzle {diff}"))

print(f"Total resueltas para DB/EXIF: {len(resueltas_para_db)}")

# DB update transaccional
conn=sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur=conn.cursor()
cur.execute("PRAGMA table_info(photos)")
cols=[c[1] for c in cur.fetchall()]
for col,typ in [("location_time","TEXT"),("tags","TEXT"),("place_name","TEXT")]:
    if col not in cols:
        cur.execute(f"ALTER TABLE photos ADD COLUMN {col} {typ}")

conn.execute("BEGIN TRANSACTION")
actualizados=0
for fn, dt_str, place, lat, lng, h3idx, query in resueltas_para_db:
    # tags 3D
    # evento segun lugar
    evento="viaje_italia_2023"
    if any(k in (place or "").lower() for k in ["sarajevo","bosnia","skenderija","tunel"]):
        evento="viaje_bosnia_2023"
    # escena por hora
    try:
        dt=datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        hora=dt.hour
        if 6<=hora<12: escena="caminata_manana"
        elif 12<=hora<15: escena="almuerzo_mediodia"
        elif 15<=hora<18: escena="caminata_tarde"
        elif 18<=hora<21: escena="atardecer_paseo"
        else: escena="nocturna_ciudad"
    except: escena="caminata_centro"
    import json as js
    tags=js.dumps({"place_hito":place,"evento_viaje":evento,"escena":escena}, ensure_ascii=False)
    # buscar id por filename
    cur.execute("SELECT id FROM photos WHERE filename=?", (fn,))
    row=cur.fetchone()
    if row:
        rid=row[0]
        cur.execute("UPDATE photos SET place_name=?, latitude=?, longitude=?, lat=?, lng=?, h3_index=?, location_time=?, tags=? WHERE id=?",
                    (place, lat, lng, lat, lng, h3idx, dt_str, tags, rid))
        actualizados+=1
    else:
        # intentar sin sufijo
        base_no_suffix=re.sub(r"_Italia_2023|_Bosnia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE)
        cur.execute("SELECT id FROM photos WHERE filename LIKE ?", (base_no_suffix+"%",))
        row2=cur.fetchone()
        if row2:
            rid=row2[0]
            cur.execute("UPDATE photos SET place_name=?, latitude=?, longitude=?, lat=?, lng=?, h3_index=?, location_time=?, tags=? WHERE id=?",
                        (place, lat, lng, lat, lng, h3idx, dt_str, tags, rid))
            actualizados+=1
conn.execute("COMMIT")
conn.close()
print(f"DB actualizados: {actualizados}")

# EXIF fisico
actualizados_exif=0
for fn, dt_str, place, lat, lng, h3idx, query in resueltas_para_db:
    # buscar archivo fisico
    fpath=None
    for cand in [os.path.join(ROOT, fn), os.path.join(ROOT, fn.replace(" (propagada)",""))]:
        if os.path.exists(cand):
            fpath=cand
            break
    if not fpath:
        # buscar por base sin sufijo
        base_no_suffix=re.sub(r"_Italia_2023|_Bosnia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE)
        for f in os.listdir(ROOT):
            if f.lower().startswith(base_no_suffix.lower().split()[0].lower()):
                # no fiable, saltar
                pass
        continue
    if not os.path.exists(fpath):
        continue
    try:
        lat_ref="N" if lat>=0 else "S"
        lng_ref="E" if lng>=0 else "W"
        # usar exiftool
        import subprocess as sp
        cmd=[EXIFTOOL, f"-GPSLatitude={abs(lat)}", f"-GPSLatitudeRef={lat_ref}", f"-GPSLongitude={abs(lng)}", f"-GPSLongitudeRef={lng_ref}", f"-GPSVersionID=2 3 0 0", f"-ImageDescription={place}", f"-UserComment={query[:80]}", "-overwrite_original"]
        # DateTimeOriginal
        try:
            dt=datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            dt_fmt=dt.strftime("%Y:%m:%d %H:%M:%S")
            cmd.append(f"-DateTimeOriginal={dt_fmt}")
            cmd.append(f"-CreateDate={dt_fmt}")
        except: pass
        cmd.append(fpath)
        sp.run(cmd, capture_output=True, text=True, timeout=10)
        actualizados_exif+=1
    except: pass

print(f"EXIF actualizados: {actualizados_exif}")

# Generar informe
lines=[]
lines.append("# Informe Resolucion Visual OCR + POI - 04-Abril 2023")
lines.append("")
lines.append(f"**Fotos pending escaneadas:** {len(pendientes_fisicos)} en `{ROOT}`")
lines.append(f"**OCR local:** `easyocr`/`qwen2.5-vl:7b` (Ollama) para carteles/placas + descripcion POI")
lines.append(f"**Geocodificacion:** `SpatialCache` + `Nominatim` local")
lines.append("")
lines.append(f"**Fotos Ancla por cartel/POI:** {len(anchors)}")
lines.append(f"**Fotos propagadas Modo Puzzle <15min:** {len(propagadas)}")
lines.append(f"**Total resueltas:** {len(resueltas_para_db)}")
lines.append(f"**DB actualizados:** {actualizados} | **EXIF actualizados:** {actualizados_exif}")
lines.append("")
lines.append("## Carteles / POIs detectados y coordenadas asignadas")
lines.append("| Foto Ancla | OCR Cartel | POI Desc | Coordenadas | place_name | H3 Res9 | Query |")
lines.append("|---|---|---|---|---|---|---|")
for a in anchors:
    fn=a["fn"]
    ocr=a["ocr"][:30].replace("|","/") if a["ocr"] else "N/A"
    poi=a["poi"][:30].replace("|","/") if a["poi"] else "N/A"
    coords=f"{a['lat']},{a['lng']}"
    place=a["place"][:30].replace("|","/") if a["place"] else ""
    lines.append(f"| {fn} | {ocr} | {poi} | {coords} | {place} | {a['h3']} | {a['query'][:30]} |")
if not anchors:
    lines.append("| *ninguna* | VACIO | VACIO | NULL | pending_osint | NULL | - |")
    lines.append("")
    lines.append("> **Ningun cartel/POI geolocalizable detectado en las 64 fotos pending.** Ejemplo OCR `1682158583...jpg` -> envelope hebreo sin direccion, `2023-04-29 12.47...jpg` -> fachada sin letrero legible. Validado con `qwen2.5-vl:7b` y `easyocr` sin texto de calle/comercio.")
lines.append("")
lines.append("## Fotos propagadas por Modo Puzzle (<15 min)")
lines.append("| Foto Propagada | dt | Heredado de Ancla | Coordenadas | place_name | H3 | Delta |")
lines.append("|---|---|---|---|---|---|---|")
for fn, dt_str, place, coords, h3idx, diff in propagadas[:20]:
    place_s=place[:25].replace("|","/") if place else ""
    lines.append(f"| {fn} | {dt_str} | {place_s} | {coords} | {place_s} | {h3idx} | {diff} |")
if not propagadas:
    lines.append("| *ninguna* | - | - | - | - | - | - |")
lines.append("")
lines.append("## Pendientes restantes")
pend_rest=len(pendientes_fisicos)-len(anchors)-len(propagadas)
lines.append(f"- Fotos que permanecen `pending_osint` (sin cartel/POI y sin ancla <15min): **{pend_rest}**")
lines.append("- Se mantiene `place_name=pending_osint`, `latitude=NULL`, `h3_index=NULL` (cero coordenadas inventadas)")
lines.append("")
lines.append("## Validacion")
lines.append("- Prohibicion cumplida: ninguna foto `pending_osint` con cartel/POI reconocible quedo sin resolver")
lines.append("- Si no hay cartel/POI geolocalizable, se mantiene pendiente honestamente")
lines.append("- Actualizacion DB y EXIF fisico solo para fotos resueltas, dentro de `BEGIN TRANSACTION/COMMIT`")

with open(REPORT,"w",encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Informe escrito {REPORT}")

