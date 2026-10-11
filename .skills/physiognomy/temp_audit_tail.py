import sys
import os
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

folder = 'F:/2023/10-Octubre'
report = 'data/audit_october_real_metadata_v2.md'
missing = open('data/audit_missing.txt', encoding='utf-8').read().splitlines()

images = [m for m in missing if m.lower().endswith(('.jpg', '.jpeg', '.png'))]
others = [m for m in missing if m not in images]
print('IMAGENES:', len(images), 'OTROS:', len(others))

done = 0
with open(report, 'a', encoding='utf-8') as out:
    for i, fn in enumerate(images):
        fp = os.path.join(folder, fn)
        try:
            r = subprocess.run(
                ['exiftool', '-T', '-filename', '-GPSLatitude',
                 '-GPSLongitude', '-ImageDescription', fp],
                capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip():
                out.write(r.stdout if r.stdout.endswith('\n') else r.stdout + '\n')
                done += 1
            else:
                out.write(fn + '\t-\t-\t-\n')
        except Exception:
            out.write(fn + '\t-\t-\t-\n')
        if (i + 1) % 10 == 0:
            print('imagenes procesadas:', i + 1)

    for fn in others:
        fp = os.path.join(folder, fn)
        try:
            r = subprocess.run(
                ['exiftool', '-T', '-filename', '-GPSLatitude',
                 '-GPSLongitude', '-ImageDescription', fp],
                capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and r.stdout.strip():
                out.write(r.stdout if r.stdout.endswith('\n') else r.stdout + '\n')
                done += 1
            else:
                out.write(fn + '\t-\t-\t-\n')
        except Exception:
            out.write(fn + '\t-\t-\t-\n')

print('ANEXADAS:', done)
