import sys, sqlite3, os
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db'
TRIP_ROOT = r'F:\2025\Octubre\Viaje Familiar de 30 dias por Argentina'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get all Argentina photos with their file paths
c.execute("SELECT id, filename, file_path, file_ext FROM photos WHERE trip_name='argentina-2025' ORDER BY date_taken")
rows = c.fetchall()
conn.close()

missing = []
for row_id, filename, file_path, file_ext in rows:
    # Check if file exists
    if file_path:
        full_path = os.path.join(TRIP_ROOT, file_path)
    else:
        full_path = os.path.join(TRIP_ROOT, filename)
    
    if not os.path.exists(full_path):
        missing.append((row_id, filename, file_path))

print(f"Total missing files: {len(missing)} out of {len(rows)}")
print("\nFirst 20 missing:")
for row_id, filename, file_path in missing[:20]:
    print(f"  ID {row_id}: {filename} -> {file_path}")
