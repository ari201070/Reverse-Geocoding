import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Delete entries that point to deduplication folders
c.execute("DELETE FROM photos WHERE trip_name='argentina-2025' AND file_path LIKE '%Papelera%'")
deleted = c.rowcount
print(f"Deleted {deleted} duplicate entries")

conn.commit()

# Verify no more Septiembre refs
c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025' AND file_path LIKE '%Septiembre%'")
remaining = c.fetchone()[0]
print(f"Remaining Septiembre refs: {remaining}")

c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025'")
total = c.fetchone()[0]
print(f"Total Argentina photos: {total}")

conn.close()
