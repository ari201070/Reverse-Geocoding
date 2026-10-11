import os, re, json, sqlite3, subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
ROOT=r"F:\2023\04-Abril"
EXIFTOOL=r"C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe"

# Cargar todos los fisicos Bosnia
fis=[f for f in os.listdir(ROOT) if f.lower().endswith((".jpg",".jpeg")) and "_Bosnia_2023" in f]
print(f"Total Bosnia fisicos: {len(fis)}")

conn=sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
if not cursor.fetchone():
    print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
    import sys
    sys.exit(1)
cur=conn.cursor()

corregidos=0
for fn in sorted(fis):
    fpath=os.path.join(ROOT, fn)
    # Buscar DB
    cur.execute("SELECT place_name, tags, latitude, longitude FROM photos WHERE filename=?", (fn,))
    row=cur.fetchone()
    if not row:
        base=re.sub(r"_Bosnia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE)
        cur.execute("SELECT place_name, tags, latitude, longitude FROM photos WHERE filename LIKE ?", (base+"%",))
        row=cur.fetchone()
    if not row:
        continue
    place, tags, lat, lng = row
    if lat is None:
        continue
    # Verificar EXIF UserComment
    try:
        r=subprocess.run([EXIFTOOL, "-s", "-UserComment", fpath], capture_output=True, text=True, timeout=5)
        out=r.stdout
        uc=""
        for line in out.split("\n"):
            if "UserComment" in line:
                uc=line.split(":",1)[1].strip() if ":" in line else ""
                break
        # Si UserComment contiene pendiente o esta vacio, corregir
        if "pendiente" in uc.lower() or "ubicacion pendiente" in uc.lower() or not uc or uc=="no tiene informacion" or "pending" in uc.lower():
            # Escribir tags limpios de DB
            clean_tags=tags or json.dumps({"place_hito":place,"evento_viaje":"viaje_bosnia_2023","escena":"caminata_tarde"}, ensure_ascii=False)
            # Asegurar que clean_tags no contiene pendiente
            if "pending" in clean_tags.lower() or "ubicacion pendiente" in clean_tags.lower():
                clean_tags=json.dumps({"place_hito":place,"evento_viaje":"viaje_bosnia_2023","escena":"caminata_tarde"}, ensure_ascii=False)
            cmd=[EXIFTOOL, f"-UserComment={clean_tags}", "-overwrite_original", fpath]
            subprocess.run(cmd, capture_output=True, timeout=10)
            print(f"Corregido {fn} UserComment: '{uc[:30]}' -> '{clean_tags[:30]}'")
            corregidos+=1
        # Tambien verificar ImageDescription
        r2=subprocess.run([EXIFTOOL, "-s", "-ImageDescription", fpath], capture_output=True, text=True, timeout=5)
        idesc=""
        for line in r2.stdout.split("\n"):
            if "ImageDescription" in line:
                idesc=line.split(":",1)[1].strip() if ":" in line else ""
                break
        if not idesc or idesc!=place:
            cmd=[EXIFTOOL, f"-ImageDescription={place}", "-overwrite_original", fpath]
            subprocess.run(cmd, capture_output=True, timeout=10)
            print(f"  ImageDescription corregido {fn}: '{idesc[:20]}' -> '{place[:20]}'")
    except Exception as e:
        print(f"Error {fn}: {e}")

# Caso especifico 2023-04-30 11.34.16 -> ya corregido arriba, pero verificar
fn="2023-04-30 11.34.16_Bosnia_2023.jpg"
fpath=os.path.join(ROOT, fn)
if os.path.exists(fpath):
    cur.execute("SELECT place_name, tags FROM photos WHERE filename=?", (fn,))
    row=cur.fetchone()
    if row:
        print(f"Caso especifico {fn}: DB place={row[0][:30]}, tags={row[1][:50]}")
        # Verificar EXIF
        r=subprocess.run([EXIFTOOL, "-s", "-UserComment", "-ImageDescription", fpath], capture_output=True, text=True, timeout=5)
        print(r.stdout[:300])

print(f"Corregidos: {corregidos}")

# Verificar que no queden pendientes con coords validas
cur.execute("SELECT filename, place_name, tags FROM photos WHERE latitude IS NOT NULL AND (tags LIKE '%pending%' OR tags LIKE '%test%' OR tags LIKE '%ubicacion pendiente%' OR tags LIKE '%Italia_2023%')")
rows=cur.fetchall()
print(f"DB con tags residuales y coords validas: {len(rows)}")
for r in rows[:5]:
    print(f"  {r[0]} {r[1][:20]} {r[2][:40]}")

conn.close()
