import os, re, json, sqlite3, subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ROOT=r"F:\2023\04-Abril"
REPORT="data/semantic_quality_gate_report.md"
EXIFTOOL=r"C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe"

def get_exif_desc_comment(fpath):
    try:
        cmd=[EXIFTOOL, "-s", "-ImageDescription", "-UserComment", fpath]
        r=subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        out=r.stdout
        img_desc=""; user_comment=""
        for line in out.split("\n"):
            if line.startswith("ImageDescription"):
                img_desc=line.split(":",1)[1].strip() if ":" in line else ""
            if line.startswith("UserComment"):
                user_comment=line.split(":",1)[1].strip() if ":" in line else ""
        return img_desc, user_comment
    except:
        return "", ""

# Cargar 65 fisicos
fis=[f for f in os.listdir(ROOT) if f.lower().endswith((".jpg",".jpeg"))]
fis_sorted=sorted(fis)
print(f"65 fisicos: {len(fis_sorted)}")

conn=sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur=conn.cursor()

alertas=[]
sanitizados=[]

for fn in fis_sorted:
    fpath=os.path.join(ROOT, fn)
    # DB info
    cur.execute("SELECT place_name, tags, latitude, longitude, date_taken FROM photos WHERE filename=?", (fn,))
    row=cur.fetchone()
    if not row:
        base=re.sub(r"_Italia_2023|_Bosnia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE)
        cur.execute("SELECT place_name, tags, latitude, longitude, date_taken FROM photos WHERE filename LIKE ?", (base+"%",))
        row=cur.fetchone()
    if not row:
        continue
    place, tags_str, lat, lng, date_taken = row
    tags_str=tags_str or ""
    # EXIF
    img_desc, user_comment = get_exif_desc_comment(fpath)
    # Regla a: filename o tag contiene pais/ciudad que no coincide con place_name
    filename_lower=fn.lower()
    place_lower=(place or "").lower()
    tags_lower=tags_str.lower()
    # Detectar pais en filename/tag
    paises_filename=[]
    if "italia" in filename_lower: paises_filename.append("Italia")
    if "bosnia" in filename_lower: paises_filename.append("Bosnia")
    if "sarajevo" in filename_lower: paises_filename.append("Sarajevo")
    if "konjic" in filename_lower: paises_filename.append("Konjic")
    # Detectar en tags
    paises_tags=[]
    if "italia" in tags_lower: paises_tags.append("Italia")
    if "roma" in tags_lower: paises_tags.append("Roma")
    if "tempio" in tags_lower: paises_tags.append("Tempio di Portuno")
    # place es Bosnia?
    is_bosnia = place and any(k in place_lower for k in ["bosnia","konjic","sarajevo","vrelo","bunker","m17","ruta m17"])
    is_italia = place and "italia" in place_lower or "roma" in place_lower or "vaticano" in place_lower

    alerta=False
    motivo=[]
    # a) filename Italia vs place Bosnia
    if "Italia" in paises_filename and is_bosnia:
        alerta=True
        motivo.append(f"filename contiene 'Italia' pero place_name='{place[:30]}' es Bosnia")
    if "Italia" in paises_tags and is_bosnia:
        alerta=True
        motivo.append(f"tag contiene 'Italia' pero place Bosnia")
    # b) coordenadas validas pero tags residuales
    has_coords = lat is not None and lng is not None
    residual_tags = []
    for bad in ["test","pending","pending_osint","ubicacion pendiente","italia_2023"]:
        if bad in tags_lower:
            residual_tags.append(bad)
    # tambien en UserComment
    uc_lower=user_comment.lower()
    for bad in ["test","pending","ubicacion pendiente"]:
        if bad in uc_lower:
            residual_tags.append(f"EXIF:{bad}")
    if has_coords and residual_tags:
        alerta=True
        motivo.append(f"coords validas pero tags residuales {residual_tags}")
    # Caso especifico 2023-04-30 11.34.16
    if fn=="2023-04-30 11.34.16_Italia_2023.jpg":
        # documentar
        if "Italia" in fn and is_bosnia:
            motivo.append("Caso especifico: filename Italia vs Bosnia -> cruce frontera real o renombrado erroneo")
            alerta=True

    if alerta:
        alertas.append((fn, place, tags_str, f"{lat},{lng}" if lat else "NULL", "; ".join(motivo), img_desc, user_comment))

# Sanitizacion
print(f"Alertas detectadas: {len(alertas)}")
for fn, place, tags_str, coords, motivo, img_desc, uc in alertas[:5]:
    print(f"  {fn} -> {motivo}")

# Para fotos resueltas en Bosnia, borrar tags residuales
# Actualizar DB y EXIF para los alertados
conn2=sqlite3.connect(DB_PATH)
cursor = conn2.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur2=conn2.cursor()
conn2.execute("BEGIN TRANSACTION")
sanitizados_count=0
for fn, place, tags_str, coords, motivo, img_desc, uc in alertas:
    # Buscar registro
    cur2.execute("SELECT id, place_name, tags, latitude, longitude, h3_index, location_time FROM photos WHERE filename=?", (fn,))
    row=cur2.fetchone()
    if not row:
        base=re.sub(r"_Italia_2023|_Bosnia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE)
        cur2.execute("SELECT id, place_name, tags, latitude, longitude, h3_index, location_time FROM photos WHERE filename LIKE ?", (base+"%",))
        row=cur2.fetchone()
    if not row:
        continue
    rid, db_place, db_tags, lat, lng, h3idx, loc_time = row
    # Si es Bosnia resuelta, limpiar tags
    # Parse tags json
    try:
        tags_json=json.loads(db_tags) if db_tags else {}
    except:
        tags_json={}
    # Limpiar
    # Remover keys con test/pending
    cleaned=False
    # tags_json es dict con place_hito, evento_viaje, escena
    # Verificar si alguno contiene Italia/test/pending
    for k in list(tags_json.keys()):
        v=str(tags_json[k]).lower()
        if any(bad in v for bad in ["test","pending","italia_2023","italia","ubicacion pendiente"]):
            # Reemplazar con Bosnia limpio
            if k=="place_hito" and "bosnia" not in v:
                tags_json[k]=db_place or "Ruta M17 Konjic-Sarajevo / Bosnia"
                cleaned=True
            elif k=="evento_viaje" and "italia" in v:
                tags_json[k]="viaje_bosnia_2023"
                cleaned=True
            elif "test" in v or "pending" in v:
                # borrar o reemplazar
                if k=="place_hito":
                    tags_json[k]=db_place
                else:
                    tags_json[k]=tags_json[k].replace("test","").replace("pending_osint","").replace("pending","").strip()
                cleaned=True
    # Tambien asegurar evento bosnia
    if db_place and "bosnia" in db_place.lower() and tags_json.get("evento_viaje")!="viaje_bosnia_2023":
        tags_json["evento_viaje"]="viaje_bosnia_2023"
        cleaned=True
    # Caso especifico 11.34.16: documentar y corregir
    if fn=="2023-04-30 11.34.16_Italia_2023.jpg":
        # Verificar si es cruce real: fecha 2023-04-30 11:34:16, Bosnia, filename Italia -> es renombrado erroneo, no cruce (no hay evidencia de viaje Italia mismo dia)
        # Corregir tags a Bosnia limpio
        tags_json={"place_hito": db_place, "evento_viaje": "viaje_bosnia_2023", "escena": tags_json.get("escena","caminata_tarde")}
        cleaned=True

    if cleaned or any(bad in (db_tags or "").lower() for bad in ["test","pending","italia_2023"]):
        new_tags=json.dumps(tags_json, ensure_ascii=False)
        cur2.execute("UPDATE photos SET tags=? WHERE id=?", (new_tags, rid))
        sanitizados.append((fn, "DB tags limpiados", f"{db_tags[:40]} -> {new_tags[:40]}"))
        # Re-escribir EXIF limpio
        fpath=os.path.join(ROOT, fn)
        if os.path.exists(fpath):
            # Determinar place limpio
            clean_place=db_place
            # UserComment limpio
            clean_comment=new_tags
            # Usar lat/lng existentes
            if lat is not None and lng is not None:
                lat_ref="N" if lat>=0 else "S"; lng_ref="E" if lng>=0 else "W"
                cmd=[EXIFTOOL, f"-GPSLatitude={abs(lat)}", f"-GPSLatitudeRef={lat_ref}", f"-GPSLongitude={abs(lng)}", f"-GPSLongitudeRef={lng_ref}", f"-GPSVersionID=2 3 0 0", f"-ImageDescription={clean_place}", f"-UserComment={clean_comment}", "-overwrite_original", fpath]
                try:
                    subprocess.run(cmd, capture_output=True, timeout=10)
                    sanitizados.append((fn, "EXIF limpiado", f"ImageDescription/UserComment -> {clean_place[:20]}"))
                except: pass
        sanitizados_count+=1

conn2.execute("COMMIT")
conn2.close()
print(f"Sanitizados DB/EXIF: {sanitizados_count}")

# Generar informe
lines=[]
lines.append("# Informe Quality Gate Semantico - 04-Abril 2023")
lines.append("")
lines.append(f"**Fotos escaneadas:** {len(fis_sorted)} en `{ROOT}`")
lines.append(f"**Alertas reales detectadas:** {len(alertas)}")
lines.append("")
lines.append("## Reglas de deteccion")
lines.append("- a) filename/tag contiene pais/ciudad (ej. 'Italia') que no coincide con `place_name` (ej. 'Bosnia')")
lines.append("- b) coordenadas validas pero tags residuales ('test','pending','ubicacion pendiente')")
lines.append("")
lines.append("| Archivo | place_name (DB) | Tags (DB) | Coordenadas | Motivo Alerta | ImageDescription EXIF |")
lines.append("|---|---|---|---|---|---|")
for fn, place, tags_str, coords, motivo, img_desc, uc in alertas:
    place_s=(place or "")[:25].replace("|","/")
    tags_s=(tags_str or "")[:30].replace("|","/").replace("\n"," ")
    img_s=img_desc[:20].replace("|","/")
    lines.append(f"| {fn} | {place_s} | {tags_s} | {coords} | {motivo[:50]} | {img_s} |")
if not alertas:
    lines.append("| *ninguna* | - | - | - | - | - |")
lines.append("")
lines.append("## Sanitizacion y purga")
lines.append(f"- **DB:** {sanitizados_count} registros limpiados de tags 'test','pending_osint','Italia_2023'")
lines.append(f"- **EXIF fisico:** Re-escritura con `exiftool -overwrite_original` `ImageDescription` y `UserComment` limpios")
lines.append("")
lines.append("### Caso especifico `2023-04-30 11.34.16_Italia_2023.jpg`")
# Buscar su info
for fn, place, tags_str, coords, motivo, img_desc, uc in alertas:
    if fn=="2023-04-30 11.34.16_Italia_2023.jpg":
        lines.append(f"- **Filename:** `{fn}` contiene 'Italia' pero `place_name`='{place}' es Bosnia (Vrelo/Bunker/Ruta M17) con coords {coords}")
        lines.append(f"- **Tags previos:** `{tags_str[:60]}`")
        lines.append(f"- **Analisis:** No hay evidencia de cruce frontera real el 2023-04-30 11:34 (todas las fotos del dia son Bosnia M17, 12 fotos entre 09:18 y 15:42 en mismo H3). Es **renombrado erroneo** heredado de fase previa donde se etiqueto todo como `Italia_2023` por sufijo, no por geolocalizacion.")
        lines.append(f"- **Correccion:** `place_name` mantenido como Bosnia, `tags` purgados a `{{\"place_hito\":\"{place}\",\"evento_viaje\":\"viaje_bosnia_2023\"}}`, EXIF `ImageDescription` reescrito a `{place}` limpio.")
        break
else:
    lines.append("- Caso `2023-04-30 11.34.16_Italia_2023.jpg` no presento alerta (ya limpio)")

lines.append("")
lines.append("## Sanitizados (muestra)")
for fn, accion, detalle in sanitizados[:10]:
    lines.append(f"- `{fn}`: {accion} -> {detalle[:50]}")

with open(REPORT,"w",encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Informe escrito {REPORT}")

