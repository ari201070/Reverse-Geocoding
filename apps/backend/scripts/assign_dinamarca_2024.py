import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)

print("--- ACTUALIZANDO TRIP_NAME A 'dinamarca-2024' PARA FOTOS DE SEPTIEMBRE 2024 ---")

# Let's check photos in F:\2024\09-Septiembre
sept_path_pattern = "%2024\\09-Septiembre%"
sept_path_pattern2 = "%2024/09-Septiembre%"

cursor = conn.execute("""
    UPDATE photos 
    SET trip_name = 'dinamarca-2024',
        country = 'Dinamarca',
        location_source = 'LOCAL_FALLBACK',
        confidence_score = 0.85
    WHERE original_path LIKE ? OR original_path LIKE ? OR final_path LIKE ? OR final_path LIKE ?
""", (sept_path_pattern, sept_path_pattern2, sept_path_pattern, sept_path_pattern2))

conn.commit()

updated_count = cursor.rowcount
print(f"Registros actualizados a 'dinamarca-2024': {updated_count}")

# Also tag physically with _Dinamarca_2024 if not present
rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = 'dinamarca-2024'").fetchall()
tagged = 0
for row in rows:
    pid = row[0]
    p = row[1].replace("\\\\", "\\")
    if os.path.exists(p):
        d, f = os.path.dirname(p), os.path.basename(p)
        base, ext = os.path.splitext(f)
        tag = "Dinamarca_2024"
        if tag not in base:
            new_f = f"{base}_{tag}{ext}"
            new_p = os.path.join(d, new_f)
            if not os.path.exists(new_p):
                os.rename(p, new_p)
            else:
                new_p = p
            conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (new_p, new_p, pid))
            tagged += 1

conn.commit()
conn.close()
print(f"Total fotos de Dinamarca etiquetadas físicamente: {tagged}")
