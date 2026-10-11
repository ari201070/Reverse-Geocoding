import sys
import os
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

EXIFTOOL = r'C:\Users\flier\AppData\Local\Programs\ExifTool\exiftool.exe'
ROOT = r'F:\2023\10-Octubre'
OUT_REPORT = r'data/italy_october_baseurl_audit.md'

def main():
    if not os.path.exists(ROOT):
        print(f"Directorio no encontrado: {ROOT}")
        return

    files = sorted([f for f in os.listdir(ROOT) if os.path.isfile(os.path.join(ROOT, f))])
    print(f"Total archivos en disco: {len(files)}")

    md = []
    md.append('# Auditoría Masiva de Persistencia BaseURL - Lote de Octubre (Italia 2023)\n')
    md.append('**Fecha de Auditoría:** Escaneo forense de solo lectura ejecutado localmente vía ExifTool (`-m` para mitigación de tráilers binarios / MP4).\n')
    md.append(f'**Total de archivos evaluados:** {len(files)}\n')
    md.append('| Archivo | Fecha / Hora (EXIF) | BaseURL Física (EXIF) | ImageDescription | Estado / Alerta |')
    md.append('| :--- | :--- | :--- | :--- | :--- |')

    # Procesar de 1 en 1 para garantizar 0 timeouts en Windows
    count = 0
    for fn in files:
        fp = os.path.join(ROOT, fn)
        cmd = [EXIFTOOL, '-T', '-m', '-n', '-filename', '-DateTimeOriginal', '-XMP-xmp:BaseURL', '-ImageDescription', fp]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
            line = res.stdout.strip()
            if not line:
                continue
            parts = line.split('\t')
            url = parts[2] if len(parts) > 2 and parts[2] != '-' else ''
            desc = parts[3] if len(parts) > 3 and parts[3] != '-' else ''
            dt = parts[1] if len(parts) > 1 and parts[1] != '-' else 'Sin EXIF DateTime'

            lower_fn = fn.lower()
            if lower_fn.endswith(('.mp4', '.mov', '.pbm', '.png', '_exiftool_tmp')) or 'vid-' in lower_fn:
                status = 'OMITIDO (Filtro -m / Formato No-JPG)'
            elif url:
                status = 'OK (Voucher Link)'
            else:
                if '2023-10-04' in fn and ('14.' in fn or '15.' in fn or '16.' in fn or '17.' in fn):
                    status = 'ALERTA: Ventana Activa sin Link'
                elif '2023-10-03' in fn and ('14.' in fn or '15.' in fn or '16.' in fn or '18.' in fn or '09.' in fn):
                    status = 'ALERTA: Ventana Activa sin Link'
                else:
                    status = 'OK (Estandar de Viaje)'

            url_clean = url.replace('|', '\\|') if url else '*(Vacío)*'
            desc_clean = desc.replace('|', '\\|') if desc else '*(Sin Descripción)*'
            md.append(f'| `{fn}` | {dt} | {url_clean} | {desc_clean} | {status} |')
            count += 1
        except Exception:
            md.append(f'| `{fn}` | Sin EXIF | *(Timeout)* | *(Timeout)* | OMITIDO (Timeout) |')

    os.makedirs(os.path.dirname(OUT_REPORT), exist_ok=True)
    with open(OUT_REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')

    print(f"Reporte de auditoría generado exitosamente: {OUT_REPORT} ({count} archivos procesados, {len(md)} lineas)")

if __name__ == '__main__':
    main()
