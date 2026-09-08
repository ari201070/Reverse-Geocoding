import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

conn = sqlite3.connect(r'F:\photo_catalog.db')
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT id, original_path FROM photos WHERE trip_name = \'slovenia-2015\'').fetchall()

tagged_count = 0
for row in rows:
    pid = row["id"]
    p = row["original_path"].replace("\\\\", "\\")
    # Normalize path separators
    p = os.path.normpath(p)
    if os.path.exists(p):
        d, f = os.path.dirname(p), os.path.basename(p)
        base, ext = os.path.splitext(f)
        if not base.endswith('_Eslovenia_2015'):
            new_f = f"{base}_Eslovenia_2015{ext}"
            new_p = os.path.join(d, new_f)
            os.rename(p, new_p)
            conn.execute('UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?', (new_p, new_p, pid))
            tagged_count += 1

conn.commit()
conn.close()
print(f"Archivos de Eslovenia etiquetados y actualizados en DB: {tagged_count}")
