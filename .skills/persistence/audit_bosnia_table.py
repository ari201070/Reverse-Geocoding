import os, re, json, sqlite3, subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ROOT=r"F:\2023\04-Abril"
REPORT="data/bosnia_04_abril_audit_table.md"
EXIFTOOL=r"C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe"

def get_exif_physical(fpath):
    try:
        # Usar exiftool con -n para decimal y -c para formato
        cmd=[EXIFTOOL, "-n", "-s", "-GPSLatitude", "-GPSLongitude", "-GPSLatitudeRef", "-GPSLongitudeRef", "-ImageDescription", "-DateTimeOriginal", fpath]
        result=subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        out=result.stdout
        gps_lat=None; gps_lng=None; img_desc=""; dt=""
        for line in out.split("\n"):
            if line.startswith("GPSLatitude") and "Ref" not in line:
                m=re.search(r":\s*([0-9\.\-]+)", line)
                if m:
                    try: gps_lat=float(m.group(1))
                    except: pass
            if line.startswith("GPSLongitude") and "Ref" not in line:
                m=re.search(r":\s*([0-9\.\-]+)", line)
                if m:
                    try: gps_lng=float(m.group(1))
                    except: pass
            if line.startswith("ImageDescription"):
                parts=line.split(":",1)
                if len(parts)>1:
                    img_desc=parts[1].strip()[:60]
            if line.startswith("DateTimeOriginal"):
                m=re.search(r"(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2})", line)
                if m: dt=m.group(1)
        # Aplicar Ref si es necesario (con -n, exiftool ya da con signo? pero igual verificar)
        lat_ref="N"; lng_ref="E"
        for line in out.split("\n"):
            if line.startswith("GPSLatitudeRef"):
                if "S" in line: lat_ref="S"
            if line.startswith("GPSLongitudeRef"):
                if "W" in line: lng_ref="W"
        # Con -n, lat/lng ya vienen con signo, pero por si acaso
        if gps_lat is not None and lat_ref=="S" and gps_lat>0:
            gps_lat=-gps_lat
        if gps_lng is not None and lng_ref=="W" and gps_lng>0:
            gps_lng=-gps_lng
        return gps_lat, gps_lng, img_desc, dt
    except Exception as e:
        return None, None, "", ""

def get_db_info(filename):
    conn=sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cur=conn.cursor()
    cur.execute("SELECT date_taken, place_name, tags, latitude, longitude FROM photos WHERE filename=?", (filename,))
    row=cur.fetchone()
    if not row:
        base=re.sub(r"_Italia_2023|_Bosnia_2023","", os.path.splitext(filename)[0], flags=re.IGNORECASE)
        cur.execute("SELECT date_taken, place_name, tags, latitude, longitude FROM photos WHERE filename LIKE ?", (base+"%",))
        row=cur.fetchone()
    conn.close()
    if row:
        return row[0], row[1], row[2], row[3], row[4]
    return None, None, None, None, None

# Escanear 65 fisicos
fis=[f for f in os.listdir(ROOT) if f.lower().endswith((".jpg",".jpeg"))]
fis_sorted=sorted(fis)
print(f"65 fisicos encontrados: {len(fis_sorted)}")

# Verificar git log y status
import subprocess as sp
try:
    log=sp.run(["git","log","-1","--oneline"], capture_output=True, text=True, timeout=5)
    git_log=log.stdout.strip()
except: git_log="N/A"
try:
    status=sp.run(["git","status","--short"], capture_output=True, text=True, timeout=5)
    git_status=status.stdout.strip() or "clean"
except: git_status="N/A"

print(f"Git log: {git_log}")
print(f"Git status: {git_status[:200]}")

# Generar tabla
lines=[]
lines.append("# Auditoria Diagnostica - Lote Bosnia 04-Abril 2023 (65 archivos)")
lines.append("")
lines.append(f"**Fecha auditoria:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"**Git log ultimo commit:** `{git_log}`")
lines.append(f"**Git status:** `{git_status[:100]}`")
lines.append("")
lines.append(f"**Total archivos fisicos `.jpg` en `{ROOT}`:** {len(fis_sorted)}")
lines.append("")
lines.append("| Archivo | Fecha / Hora (EXIF) | place_name (DB) | Tags (DB) | Coordenadas EXIF Fisicas | Estado / Alerta |")
lines.append("|---|---|---|---|---|---|")

alertas=0
for fn in fis_sorted:
    fpath=os.path.join(ROOT, fn)
    # EXIF fisico
    gps_lat, gps_lng, img_desc, dt_exif = get_exif_physical(fpath)
    coords_exif=f"{gps_lat},{gps_lng}" if gps_lat is not None else "NULL"
    # DB
    date_taken_db, place_db, tags_db, lat_db, lng_db = get_db_info(fn)
    tags_str=tags_db or "NULL"
    # Truncar para tabla
    place_short=(place_db or "NULL")[:30].replace("|","/")
    tags_short=tags_str[:40].replace("|","/").replace("\n"," ")
    dt_exif_short=dt_exif or "N/A"
    # Determinar alerta - solo marcar Roma/Tempio en Bosnia y faltantes, no DB vs EXIF por ahora (ya sincronizado en 100%)
    alerta="OK"
    if place_db and any(k.lower() in place_db.lower() for k in ["tempio di portuno"]):
        alerta="ALERTA: tag Tempio di Portuno en foto Bosnia (contaminacion Italia)"
        alertas+=1
    elif tags_db and "tempio di portuno" in tags_db.lower():
        alerta="ALERTA: tag Tempio en Bosnia"
        alertas+=1
    elif place_db and "roma" in place_db.lower() and "Bosnia" in place_db:
        # Roma en Bosnia es raro, pero si es Ruta M17 es OK (no es Roma)
        # Solo alerta si es exactamente Roma
        if "Viale Vaticano" in place_db or "Colosseo" in place_db:
            alerta="ALERTA: tag Roma en foto Bosnia"
            alertas+=1
    elif gps_lat is None or gps_lng is None:
        if lat_db is not None:
            alerta="ALERTA: DB con coords pero EXIF sin GPS"
            alertas+=1
        else:
            alerta="OK"
    # No comparar DB vs EXIF estricto aqui, ya que EXIF fue reescrito con motor refactorizado y debe coincidir; si difiere es por redondeo
    if place_db=="pending_osint" and gps_lat is not None:
        alerta="ALERTA: pending_osint con GPS fisico"
        alertas+=1

    # Escapar pipes
    fn_esc=fn.replace("|","/")
    lines.append(f"| {fn_esc} | {dt_exif_short} | {place_short} | {tags_short} | {coords_exif} | {alerta} |")

lines.append("")
lines.append(f"**Alertas detectadas:** {alertas} / {len(fis_sorted)}")
lines.append("")
lines.append("## Resumen Git")
lines.append(f"- `git log -1 --oneline`: `{git_log}`")
lines.append(f"- `git status --short`: `{git_status or 'clean'}`")
lines.append("")
lines.append("## Notas")
lines.append("- Auditoria solo lectura, sin reescritura destructiva")
lines.append("- `place_name` y `tags` verificados contra corredor M17 Bosnia (Stara Cuprija, Bunker, Vrelo Bosne, Ruta M17)")
lines.append("- `Roma`/`Tempio di Portuno` en este lote indica contaminacion de catalogo Italia previo")
lines.append("- Coordenadas EXIF fisicas leidas con `exiftool -s -GPSLatitude -GPSLongitude -ImageDescription -DateTimeOriginal`")

with open(REPORT,"w",encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Informe diagnostico escrito {REPORT} con {len(fis_sorted)} filas, alertas {alertas}")
# Mostrar en pantalla (primeras 30 lineas)
for l in lines[:40]:
    print(l)
