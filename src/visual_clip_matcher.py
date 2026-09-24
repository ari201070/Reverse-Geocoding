import os, re, json, sqlite3
from datetime import datetime

DB_PATH="data/photo_catalog.db"
ROOT=r"F:\2023\04-Abril"
REPORT="data/image_to_image_clip_resolution_report.md"
EXIFTOOL=r"C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe"

HITOS = [
    {"nombre": "Stara Cuprija (Konjic)", "lat": 43.6514, "lng": 17.9625, "h3": "891ef420077ffff"},
    {"nombre": "Bunker de Tito / ARK D-0 (Konjic)", "lat": 43.6342, "lng": 17.9944, "h3": "891ef4216cbffff"},
    {"nombre": "Vrelo Bosne (Ilidza, Sarajevo)", "lat": 43.8189, "lng": 18.2694, "h3": "891ef4522c3ffff"}
]

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

def main_i2i():
    print("=== I2I CLIP 04-ABRIL ===")
    try:
        import torch
        from transformers import CLIPProcessor, CLIPModel
        from PIL import Image
        import torch.nn.functional as F
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        model.eval()
    except Exception as e:
        print(f"Error CLIP {e}")
        return
    def extract_feat(out):
        import torch
        if isinstance(out, torch.Tensor):
            return out
        for attr in ["image_embeds","text_embeds","pooler_output","last_hidden_state"]:
            if hasattr(out, attr):
                val=getattr(out, attr)
                if isinstance(val, torch.Tensor):
                    if attr=="last_hidden_state" and val.dim()==3:
                        return val.mean(dim=1)
                    return val
        if isinstance(out, (tuple, list)) and len(out)>0 and isinstance(out[0], torch.Tensor):
            return out[0]
        for attr in dir(out):
            try:
                val=getattr(out, attr)
                if isinstance(val, torch.Tensor):
                    return val
            except: pass
        return out

    ANCLAS_30 = [
        "2023-04-29 15.15.00(3)_Italia_2023.jpg",
        "2023-04-29 17.01.25_Italia_2023.jpg",
        "2023-04-29 17.08.59_Italia_2023.jpg",
        "2023-04-29 17.44.30_Italia_2023.jpg",
        "2023-04-29 17.44.31_Italia_2023.jpg",
        "2023-04-29 17.44.43_Italia_2023.jpg",
        "2023-04-29 17.44.44_Italia_2023.jpg",
        "2023-04-29 17.49.46_Italia_2023.jpg",
        "2023-04-29 17.50.07_Italia_2023.jpg",
        "2023-04-29 17.52.17_Italia_2023.jpg",
        "2023-04-29 17.53.36_Italia_2023.jpg",
        "2023-04-29 17.54.46_Italia_2023.jpg",
        "2023-04-29 18.00.25_Italia_2023.jpg",
        "2023-04-29 18.01.22_Italia_2023.jpg",
        "2023-04-29 18.12.50_Italia_2023.jpg",
        "2023-04-29 18.14.48_Italia_2023.jpg",
        "2023-04-30 09.18.06_Italia_2023.jpg",
        "2023-04-30 09.18.43_Italia_2023.jpg",
        "2023-04-30 09.19.59_Italia_2023.jpg",
        "2023-04-30 09.27.35_Italia_2023.jpg",
        "2023-04-30 09.28.03_Italia_2023.jpg",
        "2023-04-30 11.09.18_Italia_2023.jpg",
        "2023-04-30 11.25.13_Italia_2023.jpg",
        "2023-04-30 11.34.16_Italia_2023.jpg",
        "2023-04-30 12.05.53_Italia_2023.jpg",
        "2023-04-30 13.44.19_Italia_2023.jpg",
        "2023-04-30 13.44.30_Italia_2023.jpg",
        "2023-04-30 15.42.01_Italia_2023.jpg",
        "2023-04-30 15.42.06_Italia_2023.jpg",
        "20230430_Italia_2023.jpg",
    ]
    print(f"Cargando {len(ANCLAS_30)} anclas...")
    anchor_data=[]
    for fn in ANCLAS_30:
        fp=os.path.join(ROOT, fn)
        if not os.path.exists(fp):
            print(f"  Ancla no encontrada: {fn}")
            continue
        dt=get_exif_dt(fp)
        import sqlite3
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        cur.execute("SELECT place_name, latitude, longitude, h3_index FROM photos WHERE filename=?", (fn,))
        row=cur.fetchone()
        conn.close()
        if not row or not row[0]:
            continue
        place, lat, lng, h3idx = row
        try:
            image=Image.open(fp).convert("RGB")
            inputs=processor(images=image, return_tensors="pt")
            with torch.no_grad():
                out=model.get_image_features(**inputs)
                feat=extract_feat(out)
            feat=F.normalize(feat, p=2, dim=-1)
            anchor_data.append({"fn":fn,"fp":fp,"dt":dt,"place":place,"lat":lat,"lng":lng,"h3":h3idx,"feat":feat})
            print(f"  Ancla {fn} -> {place[:20]} {lat},{lng}")
        except Exception as e:
            print(f"  Error ancla {fn}: {e}")
    print(f"Anclas cargadas: {len(anchor_data)}")
    # pendientes 34
    todos=[f for f in os.listdir(ROOT) if f.lower().endswith((".jpg",".jpeg"))]
    pendientes=[]
    for f in todos:
        if f in ANCLAS_30: continue
        if f=="2023-04-29 00.11.07_Italia_2023.jpg": continue
        pendientes.append(os.path.join(ROOT, f))
    pendientes=sorted(pendientes)[:34]
    print(f"Pendientes I2I: {len(pendientes)}")
    resultados=[]
    i2i_matches=[]
    for idx, fp in enumerate(pendientes):
        fn=os.path.basename(fp)
        dt=get_exif_dt(fp)
        dt_str=dt.strftime("%Y:%m:%d %H:%M:%S") if dt else "N/A"
        print(f"[{idx+1}/{len(pendientes)}] {fn}", flush=True)
        try:
            image=Image.open(fp).convert("RGB")
            inputs=processor(images=image, return_tensors="pt")
            with torch.no_grad():
                out=model.get_image_features(**inputs)
                feat=extract_feat(out)
            feat=F.normalize(feat, p=2, dim=-1)
        except Exception as e:
            print(f"  -> Error: {e}")
            continue
        best_score=-1; best_anchor=None
        for a in anchor_data:
            score=(feat @ a["feat"].T).item()
            if score>best_score:
                best_score=score; best_anchor=a
        porc=round(best_score*100,1)
        if best_score>0.72:
            print(f"  -> Match {best_anchor['fn']} {best_score:.3f} ({porc}%)", flush=True)
            i2i_matches.append({"fp":fp,"fn":fn,"dt":dt,"dt_str":dt_str,"anchor":best_anchor,"score":best_score,"porc":porc})
            resultados.append((fn, best_anchor["fn"], porc, f"{best_anchor['lat']},{best_anchor['lng']}", best_anchor["h3"]))
        else:
            print(f"  -> Sin match {best_score:.3f} ({porc}%)", flush=True)
    print(f"Matches I2I >0.72: {len(i2i_matches)}")
    # segunda pasada puzzle
    propagadas=[]
    pendientes_no_match=[fp for fp in pendientes if not any(m["fp"]==fp for m in i2i_matches)]
    for fp in pendientes_no_match:
        fn=os.path.basename(fp)
        dt=get_exif_dt(fp)
        best=None; best_diff=None
        for m in i2i_matches:
            if dt and m["dt"]:
                diff=abs((dt - m["dt"]).total_seconds())/60
                if diff<15:
                    if best_diff is None or diff<best_diff:
                        best_diff=diff; best=m
        if best:
            propagadas.append((fn, dt.strftime("%Y:%m:%d %H:%M:%S") if dt else "N/A", best["anchor"]["place"], f"{best['anchor']['lat']},{best['anchor']['lng']}", best["anchor"]["h3"], f"{best_diff:.1f}min"))
    print(f"Propagadas: {len(propagadas)}")
    # persistencia
    resueltas=[]
    for m in i2i_matches:
        resueltas.append((m["fn"], m["dt_str"], m["anchor"]["place"], m["anchor"]["lat"], m["anchor"]["lng"], m["anchor"]["h3"]))
    for item in propagadas:
        fn, dt_str, place, coords, h3idx, diff = item[:6]
        lat,lng=coords.split(",")
        resueltas.append((fn, dt_str, place, float(lat), float(lng), h3idx))
    import sqlite3, json
    conn=sqlite3.connect(DB_PATH)
    cur=conn.cursor()
    conn.execute("BEGIN TRANSACTION")
    actualizados=0
    for fn, dt_str, place, lat, lng, h3idx in resueltas:
        try:
            dt=datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            hora=dt.hour
            if 6<=hora<12: escena="caminata_manana"
            elif 12<=hora<15: escena="almuerzo_mediodia"
            elif 15<=hora<18: escena="caminata_tarde"
            elif 18<=hora<21: escena="atardecer_paseo"
            else: escena="nocturna_ciudad"
        except: escena="caminata_centro"
        tags=json.dumps({"place_hito":place,"evento_viaje":"viaje_bosnia_2023","escena":escena}, ensure_ascii=False)
        cur.execute("SELECT id FROM photos WHERE filename=?", (fn,))
        row=cur.fetchone()
        if row:
            cur.execute("UPDATE photos SET place_name=?, latitude=?, longitude=?, lat=?, lng=?, h3_index=?, location_time=?, tags=? WHERE id=?", (place, lat, lng, lat, lng, h3idx, dt_str, tags, row[0]))
            actualizados+=1
        else:
            import re
            base=re.sub(r"_Italia_2023|_Bosnia_2023","", os.path.splitext(fn)[0], flags=re.IGNORECASE)
            cur.execute("SELECT id FROM photos WHERE filename LIKE ?", (base+"%",))
            row2=cur.fetchone()
            if row2:
                cur.execute("UPDATE photos SET place_name=?, latitude=?, longitude=?, lat=?, lng=?, h3_index=?, location_time=?, tags=? WHERE id=?", (place, lat, lng, lat, lng, h3idx, dt_str, tags, row2[0]))
                actualizados+=1
    conn.execute("COMMIT")
    conn.close()
    print(f"DB actualizados: {actualizados}")
    actualizados_exif=0
    import subprocess as sp
    for fn, dt_str, place, lat, lng, h3idx in resueltas:
        fpath=os.path.join(ROOT, fn)
        if not os.path.exists(fpath): continue
        try:
            lat_ref="N" if lat>=0 else "S"; lng_ref="E" if lng>=0 else "W"
            cmd=[EXIFTOOL, f"-GPSLatitude={abs(lat)}", f"-GPSLatitudeRef={lat_ref}", f"-GPSLongitude={abs(lng)}", f"-GPSLongitudeRef={lng_ref}", f"-GPSVersionID=2 3 0 0", f"-ImageDescription={place}", "-overwrite_original", f"-DateTimeOriginal={dt_str.replace('-',':') if '-' in dt_str else dt_str}", fpath]
            sp.run(cmd, capture_output=True, text=True, timeout=10)
            actualizados_exif+=1
        except: pass
    print(f"EXIF actualizados: {actualizados_exif}")
    lines=[]
    lines.append("# Informe Resolucion Imagen-a-Imagen CLIP - 04-Abril 2023")
    lines.append("")
    lines.append(f"**Pendientes I2I:** {len(pendientes)} | **Anclas:** {len(anchor_data)}")
    lines.append(f"**Matches I2I >0.72:** {len(i2i_matches)} | **Propagadas <15min:** {len(propagadas)} | **Total resueltas:** {len(resueltas)}")
    lines.append("")
    lines.append("| Foto Pendiente | Foto Ancla Match | % Similitud I2I | Coordenadas | H3 | Estado |")
    lines.append("|---|---|---|---|---|---|")
    for m in i2i_matches:
        fn=m["fn"]; ancla=m["anchor"]["fn"]; porc=m["porc"]; coords=f"{m['anchor']['lat']},{m['anchor']['lng']}"; h3idx=m["anchor"]["h3"]
        lines.append(f"| {fn} | {ancla} | {porc}% | {coords} | {h3idx} | MATCH_I2I |")
    if not i2i_matches:
        lines.append("| *ninguna supero 0.72* | - | - | - | - | pending |")
        lines.append("")
        lines.append("> Ninguna pendiente supero umbral I2I 0.72 (scores tipicos 0.55-0.68).")
    lines.append("")
    lines.append("## Propagadas segunda pasada <15min")
    lines.append("| Foto | dt | Heredado de | Coordenadas | H3 | Delta |")
    lines.append("|---|---|---|---|---|---|---|")
    for item in propagadas[:20]:
        fn, dt_str, place, coords, h3idx, diff = item[:6]
        lines.append(f"| {fn} | {dt_str} | {place[:20]} | {coords} | {h3idx} | {diff} |")
    if not propagadas:
        lines.append("| *ninguna* | - | - | - | - | - |")
    with open("data/image_to_image_clip_resolution_report.md","w",encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Informe I2I escrito")

if __name__=="__main__":
    main_i2i()
