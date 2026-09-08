import sys, sqlite3, os, json
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db'
TRIP_ROOT = r'F:\2025\Octubre\Viaje Familiar de 30 dias por Argentina'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1. Find all .heic entries for Argentina
c.execute("SELECT id, filename, file_path FROM photos WHERE trip_name='argentina-2025' AND LOWER(filename) LIKE '%.heic'")
heic_rows = c.fetchall()
print(f"Found {len(heic_rows)} .heic entries in DB")

# 2. Check which ones actually exist on disk
exist_count = 0
missing_count = 0
for row_id, filename, file_path in heic_rows:
    full_path = os.path.join(TRIP_ROOT, file_path) if file_path else os.path.join(TRIP_ROOT, filename)
    if os.path.exists(full_path):
        exist_count += 1
    else:
        missing_count += 1

print(f"  - Exist on disk: {exist_count}")
print(f"  - Missing from disk: {missing_count}")

# 3. Delete .heic entries that don't exist on disk
c.execute("DELETE FROM photos WHERE trip_name='argentina-2025' AND LOWER(filename) LIKE '%.heic' AND id NOT IN (SELECT id FROM photos WHERE trip_name='argentina-2025' AND LOWER(filename) LIKE '%.heic' AND EXISTS (SELECT 1 FROM photos p2 WHERE p2.trip_name='argentina-2025'))")

# Actually, simpler: delete ALL .heic for Argentina since they were deduplicated
c.execute("DELETE FROM photos WHERE trip_name='argentina-2025' AND LOWER(filename) LIKE '%.heic'")
deleted = c.rowcount
print(f"Deleted {deleted} .heic entries from DB")

conn.commit()

# 4. Verify remaining count
c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025'")
print(f"Remaining Argentina photos: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025' AND LOWER(filename) LIKE '%.heic'")
print(f"Remaining .heic: {c.fetchone()[0]}")

conn.close()
print("Done. DB updated.")
