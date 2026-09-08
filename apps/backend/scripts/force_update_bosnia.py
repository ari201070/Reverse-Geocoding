import os
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"F:\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, original_path FROM photos WHERE trip_name = 'bosnia-2023'").fetchall()
count = 0
for row in rows:
    pid = row["id"]
    p = row["original_path"]
    if "Fotos_Organizadas" in p:
        fname = os.path.basename(p)
        base, ext = os.path.splitext(fname)
        tag = "Bosnia_2023"
        if tag not in base:
            new_f = f"{base}_{tag}{ext}"
        else:
            new_f = fname
        target_path = os.path.join(r"F:\2023\05-Mayo", new_f)
        conn.execute("UPDATE photos SET original_path = ?, final_path = ? WHERE id = ?", (target_path, target_path, pid))
        count += 1

conn.commit()
conn.close()
print(f"Total Bosnia force updated: {count}")
