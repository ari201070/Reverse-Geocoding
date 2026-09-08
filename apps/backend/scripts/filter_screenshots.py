import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Delete screenshots that are NOT Maps (no GPS utility)
c.execute("""
    DELETE FROM photos 
    WHERE trip_name='argentina-2025' 
    AND filename LIKE 'Screenshot_%'
    AND filename NOT LIKE '%Maps%'
""")
deletedScreenshots = c.rowcount

# Delete WhatsApp images (low quality)
c.execute("""
    DELETE FROM photos 
    WHERE trip_name='argentina-2025' 
    AND filename LIKE 'IMG-%WA%'
""")
deletedWA = c.rowcount

conn.commit()

# Verify
c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025'")
total = c.fetchone()[0]

c.execute("SELECT filename FROM photos WHERE trip_name='argentina-2025' AND filename LIKE 'Screenshot_%Maps%' ORDER BY date_taken")
keptMaps = c.fetchall()

print(f"Deleted: {deletedScreenshots} screenshots (non-Maps)")
print(f"Deleted: {deletedWA} WhatsApp images")
print(f"Remaining: {total} photos")
print(f"\nKept Maps screenshots ({len(keptMaps)}):")
for (fn,) in keptMaps:
    print(f"  {fn}")

conn.close()
