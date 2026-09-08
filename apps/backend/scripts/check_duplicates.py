import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Find duplicate filenames
c.execute("""
    SELECT filename, COUNT(*) as cnt 
    FROM photos 
    WHERE trip_name='argentina-2025' 
    GROUP BY filename 
    HAVING cnt > 1
    ORDER BY cnt DESC
""")
dups = c.fetchall()

print(f"Duplicate filenames: {len(dups)}")
for fn, cnt in dups[:15]:
    print(f"  {fn}: {c.execute('SELECT COUNT(*) FROM photos WHERE trip_name=\"argentina-2025\" AND filename=?', (fn,)).fetchone()[0]} copies")

# Check total
c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025'")
total = c.fetchone()[0]
print(f"\nTotal: {total}")

conn.close()
