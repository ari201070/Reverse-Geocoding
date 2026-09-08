import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

conn = sqlite3.connect(r'F:\photo_catalog.db')
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT id, original_path FROM photos WHERE trip_name = \'slovenia-2015\'').fetchall()

updated = 0
for row in rows:
    pid = row["id"]
    p = row["original_path"].replace("\\\\", "\\")
    d, f = os.path.dirname(p), os.path.basename(p)
    base, ext = os.path.splitext(f)
    
    # Check if there is a tagged version in the same folder
    # e.g. base + '_Eslovenia_2015' or similar
    tagged_candidates = [
        f"{base}_Eslovenia_2015{ext}",
        f"{base}_73702_Eslovenia_2015{ext}", # handling any unique suffix generated
    ]
    
    # Let's search if any file in 'F:\2015\07-Julio' starts with base and ends with Eslovenia_2015
    folder = r"F:\2015\07-Julio"
    matched = None
    for item in os.listdir(folder):
        if item.startswith(base) and "Eslovenia_2015" in item:
            matched = os.path.join(folder, item)
            break
            
    if matched:
        conn.execute('UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?', (matched, matched, pid))
        updated += 1
    elif os.path.exists(p):
        # If original exists, tag it now
        if not base.endswith('_Eslovenia_2015'):
            new_f = f"{base}_Eslovenia_2015{ext}"
            new_p = os.path.join(d, new_f)
            os.rename(p, new_p)
            conn.execute('UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?', (new_p, new_p, pid))
            updated += 1

conn.commit()
conn.close()
print(f"Rutas de Eslovenia actualizadas en DB con archivos etiquetados: {updated}")
