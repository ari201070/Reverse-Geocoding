import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

conn = sqlite3.connect(r'F:\photo_catalog.db')
paths = [r[0] for r in conn.execute('SELECT original_path FROM photos WHERE trip_name = \'slovenia-2015\'').fetchall()]
conn.close()

tagged_count = 0
for p in paths:
    if os.path.exists(p):
        d, f = os.path.dirname(p), os.path.basename(p)
        base, ext = os.path.splitext(f)
        if not base.endswith('_Eslovenia_2015'):
            new_f = f"{base}_Eslovenia_2015{ext}"
            new_p = os.path.join(d, new_f)
            os.rename(p, new_p)
            tagged_count += 1

print(f"Archivos etiquetados: {tagged_count}")
