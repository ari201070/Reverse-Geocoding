import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect(r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025' AND LOWER(filename) LIKE '%.heic'")
print('HEIC in DB:', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025'")
print('Total Argentina:', c.fetchone()[0])
conn.close()
