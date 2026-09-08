import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

conn = sqlite3.connect(r'F:\photo_catalog.db')
paths = [r[0] for r in conn.execute('SELECT original_path FROM photos WHERE trip_name = \'slovenia-2015\'').fetchall()]
conn.close()

found = 0
not_found = 0
for p in paths:
    if os.path.exists(p):
        found += 1
    else:
        not_found += 1

print(f"Fisicamente encontrados: {found}")
print(f"Fisicamente no encontrados: {not_found}")
