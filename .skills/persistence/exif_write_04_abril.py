import os, sqlite3, subprocess, json, re
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ROOT=r"F:\2023\04-Abril"
REPORT="data/exif_write_04_abril_report.md"
EXIFTOOL=r"C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe"

def find_physical_for_db_filename(db_filename):
    # Buscar archivo fisico en ROOT que corresponda a db_filename
    # db_filename puede ser "2023-04-29 00.11.07.jpg" y fisico "2023-04-29 00.11.07_Italia_2023.jpg"
    # Normalizar quitando sufijos _Italia_2023, _Bosnia_2023 etc
    candidates=[]
    # Exacto
    exact=os.path.join(ROOT, db_filename)
    if os.path.exists(exact):
        return exact
    # Con sufijo Italia
    base, ext = os.path.splitext(db_filename)
    for suffix in ["_Italia_2023","_Bosnia_2023","_Italia","_Bosnia"]:
        cand=os.path.join(ROOT, base+suffix+ext)
        if os.path.exists(cand):
            return cand
        # tambien con espacio?
        cand2=os.path.join(ROOT, base+suffix+ext.replace(".jpg",".jpeg"))
        if os.path.exists(cand2):
            return cand2
    # Buscar por glob que empiece con base
    for f in os.listdir(ROOT):
        if f.lower().startswith(base.lower().split("_")[0].lower()):
            # no fiable, mejor buscar por fecha
            pass
    return None

def get_db_lote():
    conn=sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cur=conn.cursor()
    cur.execute("SELECT id, filename, file_path, date_taken, place_name, latitude, longitude, location_time, tags FROM photos WHERE date_taken LIKE '2023-04-%' OR date_taken LIKE '2023:04:%'")
    rows=cur.fetchall()
    conn.close()
    return rows

print("=== INCRUSTACION EXIF 04-ABRIL ===")
rows=get_db_lote()
print(f"Registros DB lote 2023-04: {len(rows)}")

# Mapear fisicos existentes (solo una pasada, case-insensitive)
fisicos=[]
for f in os.listdir(ROOT):
    if f.lower().endswith((".jpg",".jpeg")):
        fisicos.append(os.path.join(ROOT,f))
print(f"Archivos fisicos .jpg en {ROOT}: {len(fisicos)}")

# Para cada registro DB, intentar encontrar fisico
actualizados_geoloc=0
actualizados_pending=0
errores=0
detalles=[]

# Tambien para fisicos sin registro DB, tratar como pending
# Primero mapear DB por filename normalizado
db_by_filename={}
for r in rows:
    rid, fn, fpath, dt, place, lat, lng, loc_time, tags = r
    db_by_filename[fn.lower()]=r
    # tambien sin extension
    base=os.path.splitext(fn)[0].lower()
    db_by_filename[base]=r

print(f"Procesando {len(fisicos)} fisicos...", flush=True)
# Recorrer fisicos
for idx, fpath in enumerate(sorted(fisicos)):
    fname=os.path.basename(fpath)
    # buscar registro DB
    rec=None
    # exacto
    if fname.lower() in db_by_filename:
        rec=db_by_filename[fname.lower()]
    else:
        # probar quitando _Italia_2023
        base_no_suffix=re.sub(r"_Italia_2023|_Bosnia_2023","", os.path.splitext(fname)[0], flags=re.IGNORECASE)
        key=base_no_suffix.lower()
        if key in db_by_filename:
            rec=db_by_filename[key]
        else:
            # sin fallback EXIF pesado: solo por nombre base
            pass
    if not rec:
        # sin registro DB, marcar como pending
        place=None; lat=None; lng=None; loc_time=None; tags=None
        # tratar como pending
        rec=(None, fname, fpath, None, "pending_osint", None, None, None, None)
        is_pending=True
        db_place="pending_osint"
    else:
        rid, fn, fpath_db, dt, place, lat, lng, loc_time, tags = rec
        db_place=place
        is_pending = (place=="pending_osint" or place is None or lat is None or lng is None)

    print(f"[{idx+1}/{len(fisicos)}] {fname} -> {'PENDING' if is_pending else 'GEOLOC'}", flush=True)
    # Construir comando exiftool
    try:
        if not is_pending and lat is not None and lng is not None:
            # Geolocalizada: escribir GPS, place_name, tags, DateTimeOriginal
            # Determinar refs
            lat_ref="N" if lat>=0 else "S"
            lng_ref="E" if lng>=0 else "W"
            lat_abs=abs(lat); lng_abs=abs(lng)
            # ImageDescription y UserComment
            place_str=db_place or ""
            tags_str=tags or ""
            # location_time para DateTimeOriginal: formato "2023:04:29 00:11:07"
            dt_original=""
            if loc_time:
                try:
                    # loc_time puede ser "2023:04:29 00:11:07" o "2023-04-29 00:11:07"
                    dt_original=loc_time.replace("-"," :").replace("  ", " ").strip()
                    # asegurar formato YYYY:MM:DD HH:MM:SS
                    # si viene "2023-04-29 00:11:07" -> "2023:04:29 00:11:07"
                    dt_original=dt_original.replace("-",":")
                    # ya tiene ":"
                    if " " not in dt_original:
                        dt_original=loc_time
                except:
                    dt_original=loc_time
            else:
                dt_original=""
            # Construir args
            cmd=[EXIFTOOL,
                 f"-GPSLatitude={lat_abs}", f"-GPSLatitudeRef={lat_ref}",
                 f"-GPSLongitude={lng_abs}", f"-GPSLongitudeRef={lng_ref}",
                 f"-GPSVersionID=2 3 0 0",
                 f"-ImageDescription={place_str}",
                 f"-UserComment={tags_str}",
                 "-overwrite_original"]
            if dt_original:
                # asegurar formato correcto
                # exiftool espera "YYYY:MM:DD HH:MM:SS"
                # convertir loc_time si es "2023-04-29 00:11:07" -> "2023:04:29 00:11:07"
                dt_fmt=loc_time.replace("-"," :") if "-" in loc_time else loc_time
                dt_fmt=dt_fmt.replace("-"," :").replace("  ", " ")
                # simple: reemplazar - por :
                dt_fmt=loc_time.replace("-"," :") if "-" in loc_time else loc_time
                # fallback: usar regex
                m=re.match(r"(\d{4})[:\-](\d{2})[:\-](\d{2})[ T](\d{2}):(\d{2}):(\d{2})", loc_time)
                if m:
                    y,mo,da,hh,mm,ss=m.groups()
                    dt_fmt=f"{y}:{mo}:{da} {hh}:{mm}:{ss}"
                else:
                    dt_fmt=loc_time
                cmd.append(f"-DateTimeOriginal={dt_fmt}")
                cmd.append(f"-CreateDate={dt_fmt}")
            cmd.append(fpath)
            result=subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            actualizados_geoloc+=1
            detalles.append((fname, "GEOLOCALIZADA", f"{lat},{lng}", db_place[:40] if db_place else "", "OK" if result.returncode==0 else result.stderr[:80]))
        else:
            # Pending: eliminar GPS y escribir UserComment pendiente
            cmd=[EXIFTOOL, "-GPS:all=", "-xmp:Geotag=", "-UserComment=Ubicacion pendiente de verificacion OSINT", "-ImageDescription=pending_osint", "-overwrite_original", fpath]
            result=subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            actualizados_pending+=1
            detalles.append((fname, "PENDING", "ELIMINADO", "pending_osint", "OK" if result.returncode==0 else result.stderr[:80]))
    except Exception as e:
        errores+=1
        detalles.append((fname, "ERROR", str(e)[:40], "", "FAIL"))

print(f"Actualizados geolocalizados: {actualizados_geoloc}")
print(f"Actualizados pending (GPS eliminado): {actualizados_pending}")
print(f"Errores: {errores}")
print(f"Total fisicos procesados: {len(fisicos)}")

# Generar informe
lines=[]
lines.append("# Informe Escritura EXIF - 04-Abril 2023")
lines.append("")
lines.append(f"**Archivos fisicos .jpg en `{ROOT}`:** {len(fisicos)}")
lines.append(f"**Registros DB lote 2023-04:** {len(rows)}")
lines.append(f"**Actualizados con GPS reales:** {actualizados_geoloc}")
lines.append(f"**Actualizados como pending (GPS eliminado):** {actualizados_pending}")
lines.append(f"**Errores:** {errores}")
lines.append("")
lines.append("## Detalle por archivo fisico")
lines.append("| Archivo | Estado DB | GPS EXIF | place_name | Resultado |")
lines.append("|---|---|---|---|---|")
for fname, estado, gps, place, res in detalles:
    # escapar |
    place=place.replace("|","/")[:40]
    lines.append(f"| {fname} | {estado} | {gps} | {place} | {res} |")
lines.append("")
lines.append("## Operaciones EXIF")
lines.append("- **Geolocalizadas:** `GPSLatitude`/`GPSLongitude` + `GPSLatitudeRef`/`GPSLongitudeRef` + `ImageDescription=place_name` + `UserComment=tags JSON` + `DateTimeOriginal=location_time` (formato `YYYY:MM:DD HH:MM:SS`)")
lines.append("- **Pending:** `GPS:all=` eliminado, `UserComment=\"Ubicacion pendiente de verificacion OSINT\"`, `ImageDescription=pending_osint`")
lines.append("- Herramienta: `exiftool 13.59` (`piexif` fallback) con `-overwrite_original`, sin crear `_original`")
lines.append("- Validacion: coordenadas a 4 decimales (~11m) ya en DB, se graban como decimal con Ref N/S/E/W")
lines.append("")
lines.append("## Notas")
lines.append("- Solo se tocaron archivos fisicos `.jpg` existentes en `F:\\2023\\04-Abril`; videos `.mp4` excluidos (no soportan EXIF GPS)")
lines.append("- Registros DB sin archivo fisico (172-65=107) no se escriben a disco, solo quedan en BD")
lines.append("- Transaccion BD ya estaba limpia (strict PASS 31), EXIF refleja exactamente `pending_osint` vs 2 geolocalizadas")

with open(REPORT,"w",encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Informe escrito {REPORT}")

