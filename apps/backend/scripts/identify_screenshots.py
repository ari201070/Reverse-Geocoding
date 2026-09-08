import sys, sqlite3, os
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\flier\GitHub\viaje-argentina-octubre-2025\legacy\photo_catalog.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Find screenshot patterns
patterns = [
    "Screenshot%",
    "screenshot%",
    "%Screen%",
    "%screen%",
    "IMG-2025%WA%",  # WhatsApp images
    "Screenshot_%",
]

print("=== Capturas de pantalla detectadas ===\n")

total_screenshots = 0
for pattern in patterns:
    c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025' AND filename LIKE ?", (pattern,))
    count = c.fetchone()[0]
    if count > 0:
        print(f"Pattern '{pattern}': {count} fotos")
        total_screenshots += count

# Also check for very small files or specific patterns
c.execute("""
    SELECT filename FROM photos 
    WHERE trip_name='argentina-2025' 
    AND (filename LIKE 'Screenshot_%' OR filename LIKE 'Screenshot-%')
    ORDER BY date_taken
    LIMIT 20
""")
samples = c.fetchall()
print(f"\n=== Muestra de capturas (primeras 20) ===")
for (fn,) in samples:
    print(f"  {fn}")

c.execute("SELECT COUNT(*) FROM photos WHERE trip_name='argentina-2025'")
total = c.fetchone()[0]
print(f"\nTotal fotos: {total}")
print(f"Capturas de pantalla: {total_screenshots}")
print(f"Fotos reales: {total - total_screenshots}")

conn.close()
