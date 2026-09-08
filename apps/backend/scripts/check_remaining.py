import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check remaining Septiembre refs
c.execute("SELECT id, filename, file_path FROM photos WHERE trip_name='argentina-2025' AND file_path LIKE '%Septiembre%'")
remaining = c.fetchall()
print(f"Remaining Septiembre refs: {len(remaining)}")
for row_id, filename, file_path in remaining:
    print(f"  ID {row_id}: {filename}")
    print(f"    Path: {file_path}")

conn.close()
