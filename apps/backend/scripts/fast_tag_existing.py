import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

TRIP_TAG_MAPPINGS = {
    "argentina-2011": "Argentina_2011",
    "bosnia-2023": "Bosnia_2023",
    "montenegro-2010": "Croacia_Montenegro_2010",
    "creta-2013": "Creta_2013",
    "italia-2023": "Italia_2023",
    "slovenia-2015": "Eslovenia_2015",
    "argentina-2025": "Argentina_2025",
    "israel-2023": "Israel_2023"
}

print("--- ETIQUETADO RÁPIDO Y SEGURO (SOLO EXISTENTES) ---")

for trip_code, tag in TRIP_TAG_MAPPINGS.items():
    rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = ?", (trip_code,)).fetchall()
    count = 0
    for row in rows:
        pid = row["id"]
        p = row["original_path"].replace("\\\\", "\\")
        if os.path.exists(p):
            d, f = os.path.dirname(p), os.path.basename(p)
            base, ext = os.path.splitext(f)
            if tag not in base:
                new_f = f"{base}_{tag}{ext}"
                new_p = os.path.join(d, new_f)
                if not os.path.exists(new_p):
                    os.rename(p, new_p)
                else:
                    new_p = p
                conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (new_p, new_p, pid))
                count += 1
    print(f"Viaje {trip_code}: {count} fotos etiquetadas.")

conn.commit()
conn.close()
print("¡Listo!")
