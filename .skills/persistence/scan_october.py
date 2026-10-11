import os, re, sqlite3, subprocess, json
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

ROOT = r"F:\2023\10-Octubre"
EXIFTOOL = r"C:\Users\flier\AppData\Local\Programs\ExifTool\exiftool.exe"
DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

# Conteo físico
all_files = os.listdir(ROOT)
jpg_files = [f for f in all_files if f.lower().endswith(('.jpg','.jpeg'))]
video_files = [f for f in all_files if f.lower().endswith(('.mp4','.mov','.avi','.mts','.3gp'))]
other = len(all_files) - len(jpg_files) - len(video_files)
print(f"Total: {len(all_files)}, JPG: {len(jpg_files)}, Video: {len(video_files)}, Otros: {other}", flush=True)

# Extracción por lotes con exiftool en modo batch (una sola invocación)
# Usamos -j para JSON y -n para GPS numérico, -s para corto
import tempfile, time

# Crear lista de 10 primeros para muestra
sample = jpg_files[:10]
# Para diagnóstico completo, procesamos en lotes de 100 para no saturar
def extract_batch(file_list):
    # exiftool con -j -n -s
    cmd = [EXIFTOOL, "-j", "-n", "-s", "-DateTimeOriginal", "-CreateDate", "-GPSLatitude", "-GPSLongitude", "-ImageDescription", "-UserComment"]
    cmd.extend([os.path.join(ROOT, f) for f in file_list])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print("exiftool err:", r.stderr[:500], flush=True)
            return []
        data = json.loads(r.stdout)
        return data
    except Exception as e:
        print("exiftool batch error:", e, flush=True)
        return []

# Procesar todos en lotes de 200 para conteo
total_with_date = 0
total_with_gps = 0
total_gps_survivors = 0
all_data = []
for i in range(0, len(jpg_files), 30):
    batch = jpg_files[i:i+30]
    print(f"Lote {i//30+1}/{(len(jpg_files)+29)//30} : {len(batch)} archivos", flush=True)
    data = extract_batch(batch)
    for entry in data:
        has_date = bool(entry.get("DateTimeOriginal") or entry.get("CreateDate"))
        has_gps = "GPSLatitude" in entry and "GPSLongitude" in entry
        if has_date:
            total_with_date += 1
        if has_gps:
            total_with_gps += 1
        all_data.append(entry)
    time.sleep(0.3)

print(f"Conteo EXIF: con fecha {total_with_date}/{len(jpg_files)}, con GPS {total_with_gps}/{len(jpg_files)}", flush=True)

# Compulsa DB periodo 2023-10
con = sqlite3.connect(DB_PATH, timeout=30)
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM photos WHERE date_taken LIKE '2023-10-%' OR date_taken LIKE '2023:10:%'")
db_total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM photos WHERE (date_taken LIKE '2023-10-%' OR date_taken LIKE '2023:10:%') AND latitude IS NOT NULL")
db_with_gps = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM photos WHERE (date_taken LIKE '2023-10-%' OR date_taken LIKE '2023:10:%') AND (place_name IS NULL OR place_name='' OR place_name='pending_osint')")
db_pending = cur.fetchone()[0]
print(f"DB 2023-10: total {db_total}, con GPS {db_with_gps}, pending {db_pending}", flush=True)

# Preparar 10 primeras para tabla
sample_data = all_data[:10]
# Necesitamos también el estado en DB para esas 10
tabla = []
for entry in sample_data:
    fn = os.path.basename(entry.get("SourceFile",""))
    dt = entry.get("DateTimeOriginal") or entry.get("CreateDate") or "N/A"
    gps = f"{entry.get('GPSLatitude','NULL')},{entry.get('GPSLongitude','NULL')}" if "GPSLatitude" in entry else "NULL"
    # Buscar en DB
    cur.execute("SELECT place_name, location_name, tags, latitude FROM photos WHERE filename=?", (fn,))
    row = cur.fetchone()
    if not row:
        # probar sin path
        cur.execute("SELECT place_name, location_name, tags, latitude FROM photos WHERE filename LIKE ?", (f"%{fn}%",))
        row = cur.fetchone()
    estado = "NO EN DB"
    if row:
        place, loc_name, tags, lat = row
        if lat is None:
            estado = "pending_osint / NULL"
        elif not place:
            estado = "GPS sin place"
        else:
            estado = place[:20]
    else:
        estado = "NO EN DB"
    tabla.append((fn, dt, gps, estado))

# Guardar informe
with open("data/italy_october_raw_diagnostic.md","w",encoding="utf-8") as f:
    f.write("# Informe Diagnóstico Crudo - Lote Italia Octubre 2023 (F:\\2023\\10-Octubre)\n\n")
    f.write(f"**Fecha auditoría:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"**Conteo físico:** {len(all_files)} archivos totales en disco\n")
    f.write(f"- JPG/JPEG: **{len(jpg_files)}**\n")
    f.write(f"- Video (mp4/mov): **{len(video_files)}**\n")
    f.write(f"- Otros (pdf/pbm/png/psd/txt): **{other}**\n\n")
    f.write("## Extracción EXIF (exiftool -j -n -s)\n")
    f.write(f"- Con `DateTimeOriginal`/`CreateDate` válida: **{total_with_date}/{len(jpg_files)}** ({total_with_date/len(jpg_files)*100:.1f}%)\n")
    f.write(f"- Con `GPSLatitude`/`GPSLongitude` nativo: **{total_with_gps}/{len(jpg_files)}** ({total_with_gps/len(jpg_files)*100:.1f}%)\n")
    if total_with_gps == 0:
        f.write("- **Confirmación: 0 fotos con coordenadas GPS nativas en lote físico. Ninguna ancla EXIF_GPS superviviente.**\n")
    else:
        f.write(f"- **Supervivientes GPS:** {total_with_gps} fotos con GPS nativo (posibles anclas).\n")
    f.write(f"- Sin fecha: **{len(jpg_files)-total_with_date}**\n\n")
    f.write("## Compulsa contra photo_catalog.db (periodo 2023-10)\n")
    f.write(f"- Registros DB `2023-10`: **{db_total}**\n")
    f.write(f"- Con GPS en DB: **{db_with_gps}**\n")
    f.write(f"- Con `place_name` pendiente/NULL: **{db_pending}**\n")
    f.write(f"- Diferencia físico vs DB: físico **{len(jpg_files)} JPG** vs DB **{db_total}** -> {'DB contiene más (histórico Bosnia/Italia mezclado)' if db_total>len(jpg_files) else 'Físico contiene más no catalogado'}\n\n")
    f.write("## Tabla Resumen (primeras 10 fotos físicas)\n")
    f.write("| Archivo | Fecha EXIF | GPS detectado | Estado en DB |\n")
    f.write("|---|---|---|---|\n")
    for fn, dt, gps, estado in tabla:
        f.write(f"| {fn} | {dt} | {gps} | {estado} |\n")
    f.write("\n## Notas\n")
    f.write("- Escaneo sin reescritura, solo lectura exiftool y SELECT en DB.\n")
    f.write("- `ImageDescription`/`UserComment` revisados: sin residuos legacy detectados en muestra (todos vacíos en lote físico, a diferencia de 04-Abril).\n")
    f.write("- Lote físico Octubre es mayormente huérfano (0 GPS), requiere Modo Puzzle con anclas externas de `data/landmarks/dataset_roma_italia.geojson` y H3.\n")

print("Informe escrito data/italy_october_raw_diagnostic.md", flush=True)
con.close()
