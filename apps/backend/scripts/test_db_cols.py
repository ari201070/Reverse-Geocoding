import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(photos)")
cols = [r[1] for r in cur.fetchall()]
print("Columnas en photos:", cols)

cur.execute("SELECT location_name, location_address, city, country FROM photos WHERE trip_name='argentina-2025' LIMIT 5")
for row in cur.fetchall():
    print(row)

conn.close()
