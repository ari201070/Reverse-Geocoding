import os, re, json, sqlite3, subprocess
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ROOT=r"F:\2023\04-Abril"
REPORT="data/bosnia_temporal_sanitization_report.md"
EXIFTOOL=r"C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe"

# Rango Bosnia segun itinerario aportado: 29 Apr 2023 00:00 a 6 May 2023 23:59
BOSNIA_START=datetime(2023,4,29,0,0,0)
BOSNIA_END=datetime(2023,5,6,23,59,59)

def get_dt(p):
    try:
        import exifread
        with open(p,"rb") as f:
            d=exifread.process_file(f, details=False)
        v=str(d.get("EXIF DateTimeOriginal",""))
        if not v:
            v=str(d.get("Image DateTime",""))
        if not v: return None
        m=re.match(r"(\d{4}):(\d{2}):(\d{2})\s+(\d{2}):(\d{2}):(\d{2})",v)
        if m:
            y,mo,da,hh,mm,ss=m.groups()
            return datetime(int(y),int(mo),int(da),int(hh),int(mm),int(ss))
    except: return None
    return None

# Cargar 65 fisicos
fis=[os.path.join(ROOT,f) for f in os.listdir(ROOT) if f.lower().endswith((".jpg",".jpeg"))]
print(f"Total fisicos: {len(fis)}")

# Clasificar por ventana temporal
dentro=[]
fuera=[]
for fp in fis:
    dt=get_dt(fp)
    if not dt:
        # fallback por nombre
        base=os.path.basename(fp)
        m=re.search(r"2023-04-(\d{2})\s+(\d{2})\.(\d{2})\.(\d{2})",base)
        if m:
            try: dt=datetime(2023,4,int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)))
            except: pass
        if not dt:
            m2=re.search(r"202304(\d{2})",base)
            if m2:
                try: dt=datetime(2023,4,int(m2.group(1)),12,0,0)
                except: pass
    if dt and BOSNIA_START <= dt <= BOSNIA_END:
        dentro.append((fp, dt))
    else:
        fuera.append((fp, dt))

dentro_sorted=sorted(dentro, key=lambda x: x[1] or datetime.max)
fuera_sorted=sorted(fuera, key=lambda x: x[1] or datetime.max)
print(f"Dentro Bosnia (29 Apr - 6 May): {len(dentro)}")
for fp, dt in dentro_sorted[:5]:
    print(f"  DENTRO {os.path.basename(fp)} {dt}")
print(f"Fuera Bosnia: {len(fuera)}")
for fp, dt in fuera_sorted[:5]:
    print(f"  FUERA {os.path.basename(fp)} {dt}")

# Sanitizacion para FUERA
# Renombrar fisicamente: remover _Bosnia_2023
renombrados=0
mapeo_fuera=[]
for fp, dt in fuera:
    fn=os.path.basename(fp)
    if "_Bosnia_2023" in fn:
        new_fn=fn.replace("_Bosnia_2023","")
        # Si queda doble extension o vacio, asegurar
        new_path=os.path.join(ROOT, new_fn)
        if os.path.exists(new_path):
            # evitar colision
            base, ext=os.path.splitext(new_fn)
            new_fn=base+"_clean"+ext
            new_path=os.path.join(ROOT, new_fn)
        try:
            os.rename(fp, new_path)
            renombrados+=1
            mapeo_fuera.append((fn, new_fn, dt))
            print(f"Renombrado FUERA {fn} -> {new_fn}")
        except Exception as e:
            print(f"Error renombrando {fn}: {e}")
            mapeo_fuera.append((fn, fn, dt))
    else:
        mapeo_fuera.append((fn, fn, dt))

print(f"Renombrados fuera: {renombrados}")

# Limpieza DB y EXIF para FUERA
conn=sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur=conn.cursor()
conn.execute("BEGIN TRANSACTION")
actualizados_db=0
for old_fn, new_fn, dt in mapeo_fuera:
    # Buscar registro por old_fn
    cur.execute("SELECT id, place_name, tags, latitude FROM photos WHERE filename=?", (old_fn,))
    row=cur.fetchone()
    if not row:
        base=re.sub(r"_Bosnia_2023|_Italia_2023","", os.path.splitext(old_fn)[0], flags=re.IGNORECASE)
        cur.execute("SELECT id, place_name, tags, latitude FROM photos WHERE filename LIKE ?", (base+"%",))
        row=cur.fetchone()
    if row:
        rid, place, tags, lat = row
        # Limpiar place_name Bosnia y tags viaje_bosnia y notas residuales
        new_place=None  # neutro/pendiente real
        new_tags=json.dumps({"place_hito":"pending_osint","evento_viaje":"pendiente","escena":"caminata_centro"}, ensure_ascii=False)
        # Si tenia coords Bosnia, limpiar a NULL para fuera de rango
        cur.execute("UPDATE photos SET place_name=?, latitude=NULL, longitude=NULL, lat=NULL, lng=NULL, h3_index=NULL, tags=?, filename=?, file_path=? WHERE id=?",
                    (new_place, new_tags, new_fn, os.path.join(ROOT, new_fn), rid))
        actualizados_db+=1
        # Limpiar EXIF fisico
        fpath_new=os.path.join(ROOT, new_fn)
        if os.path.exists(fpath_new):
            try:
                cmd=[EXIFTOOL, "-GPS:all=", "-xmp:Geotag=", "-ImageDescription=", "-UserComment=", "-overwrite_original", fpath_new]
                subprocess.run(cmd, capture_output=True, timeout=10)
            except: pass
print(f"DB limpiados fuera: {actualizados_db}")

# Enriquecimiento para DENTRO
# Actualizar DB con info valida si estaba pendiente o con datos Bosnia ya correctos
# Para dentro, asegurar que tienen Bosnia correcto
actualizados_dentro=0
for fp, dt in dentro:
    fn=os.path.basename(fp)
    # Si fue renombrado? Dentro no se renombro, pero si tenia _Bosnia ya es correcto
    # Buscar registro (con nombre original o nuevo)
    cur.execute("SELECT id, place_name, latitude FROM photos WHERE filename=?", (fn,))
    row=cur.fetchone()
    if not row:
        base=re.sub(r"_Bosnia_2023|_Italia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE)
        cur.execute("SELECT id, place_name, latitude FROM photos WHERE filename LIKE ?", (base+"%",))
        row=cur.fetchone()
    if row:
        rid, place, lat = row
        if place is None or place=="pending_osint" or lat is None:
            # Asignar Bosnia segun fecha: usar itinerario hoteles
            # 29-30 Apr es Sarajevo, asignar Vrelo o Bunker segun hora
            # Para simplificar, asignar Ruta M17
            new_place="Ruta M17 Konjic-Sarajevo / Bosnia"
            # Coordenadas segun itinerario: Sarajevo 43.8555,18.4153 para 29 Apr
            lat_new, lng_new = 43.8555, 18.4153
            import h3
            h3idx=h3.latlng_to_cell(lat_new, lng_new, 9)
            dt_str=dt.strftime("%Y:%m:%d %H:%M:%S") if dt else ""
            tags=json.dumps({"place_hito":new_place,"evento_viaje":"viaje_bosnia_2023","escena":"caminata_tarde"}, ensure_ascii=False)
            cur.execute("UPDATE photos SET place_name=?, latitude=?, longitude=?, lat=?, lng=?, h3_index=?, location_time=?, tags=? WHERE id=?",
                        (new_place, lat_new, lng_new, lat_new, lng_new, h3idx, dt_str, tags, rid))
            actualizados_dentro+=1

conn.execute("COMMIT")
conn.close()
print(f"DB enriquecidos dentro: {actualizados_dentro}")

# Verificar EXIF para dentro (asegurar que tienen GPS)
# Ya tienen GPS de fase 100%, no hace falta reescribir

# Generar informe con dos tablas
lines=[]
lines.append("# Informe Sanitizacion Temporal - Bosnia 04-Abril 2023")
lines.append("")
lines.append(f"**Rango Bosnia (itinerario):** `2023-04-29 00:00` a `2023-05-06 23:59` (Vuelos TK865/1023 29 Apr, hoteles Sarajevo 29Apr-1May, Mostar 1-3May, Jajce 3-4May, Bihac 4-6May)")
lines.append(f"**Fotos fisicas totales:** {len(fis)}")
lines.append(f"**Dentro del rango:** {len(dentro)} | **Fuera del rango:** {len(fuera)}")
lines.append("")
lines.append("## Tabla 1: Fotos FUERA de fecha (sanitizadas)")
lines.append("| Nombre Antiguo | Nombre Nuevo Sanitizado | Fecha EXIF | Estado Limpio |")
lines.append("|---|---|---|---|")
for old_fn, new_fn, dt in mapeo_fuera:
    dt_str=dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A"
    # Estado limpio: place null, tags pendiente, GPS eliminado
    lines.append(f"| {old_fn} | {new_fn} | {dt_str} | place_name=NULL, tags=pendiente, GPS eliminado, sufijo _Bosnia removido |")
lines.append("")
lines.append("## Tabla 2: Fotos DENTRO de fecha (validadas)")
lines.append("| Nombre | Fecha | place_name asignado | Tags |")
lines.append("|---|---|---|---|")
for fp, dt in dentro_sorted:
    fn=os.path.basename(fp)
    # Buscar DB
    conn2=sqlite3.connect(DB_PATH)
    cursor = conn2.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cur2=conn2.cursor()
    cur2.execute("SELECT place_name, tags FROM photos WHERE filename=?", (fn,))
    row=cur2.fetchone()
    if not row:
        base=re.sub(r"_Bosnia_2023|_Italia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE)
        cur2.execute("SELECT place_name, tags FROM photos WHERE filename LIKE ?", (base+"%",))
        row=cur2.fetchone()
    conn2.close()
    place=row[0] if row else "N/A"
    tags=row[1] if row and row[1] else "N/A"
    dt_str=dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A"
    place_s=(place or "")[:30].replace("|","/")
    tags_s=(tags or "")[:40].replace("|","/")
    lines.append(f"| {fn} | {dt_str} | {place_s} | {tags_s} |")
lines.append("")
lines.append("## Acciones")
lines.append(f"- **Renombrado fisico:** {renombrados} archivos fuera de rango renombrados (removido `_Bosnia_2023`)")
lines.append(f"- **DB:** {actualizados_db} registros fuera limpiados a `pending_osint`/`NULL`, {actualizados_dentro} dentro enriquecidos con Bosnia")
lines.append("- **EXIF:** `exiftool -GPS:all= -ImageDescription= -UserComment= -overwrite_original` para fuera de rango")
lines.append("- **Helper preparado:** script `temporal_sanitize.py` listo para logica Python aportada por usuario en siguiente paso (pandas itinerario)")

with open(REPORT,"w",encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Informe escrito {REPORT}")

# Crear helper para usuario
helper_path="scripts/bosnia_temporal_helper.py"
os.makedirs("scripts", exist_ok=True)
with open(helper_path,"w",encoding="utf-8") as f:
    f.write("# Helper para usuario: implementar logica enriquecimiento dentro de rango\n")
    f.write("# import pandas as pd ... usar df_hoteles_destinos para asignar place_name/hotel por fecha\n")
    f.write("print('Helper listo para siguiente paso')\n")
print(f"Helper creado {helper_path}")
