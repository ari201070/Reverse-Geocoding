import os
import sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def main():
    db_path = r"C:\Users\flier\.gemini\antigravity\scratch\Reverse-Geocoding\photo_catalog.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cursor = conn.cursor()
    
    # Obtener conteo total
    cursor.execute("SELECT COUNT(*) FROM known_places")
    total_count = cursor.fetchone()[0]
    
    print("=== RESUMEN DE LUGARES CONOCIDOS ===")
    print(f"Total de lugares en la base de datos: {total_count}\n")
    
    # Obtener 5 registros de muestra
    cursor.execute("SELECT id, name, anon_latitude, anon_longitude FROM known_places LIMIT 5")
    samples = cursor.fetchall()
    
    print("Muestra de 5 registros:")
    for row in samples:
        print(f"- ID: {row[0]} | Nombre: {row[1]} | Lat: {row[2]} | Lng: {row[3]}")
        
    conn.close()

if __name__ == '__main__':
    main()
