import os
import sys
import io
import sqlite3

# Set UTF-8 output to avoid Windows console encoding errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

def main():
    print("=== INICIANDO PIPELINE DE LIMPIEZA Y DEDUPLICACIÓN EXACTA ===")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    try:
        # Check starting state
        start_count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        print(f"Total registros iniciales: {start_count}")
        
        print("\n--- 1. Depuración de Papelera y Basura de Disco ---")
        conn.execute("BEGIN TRANSACTION;")
        
        # We delete:
        # - folder_source is 'papelera'
        # - folder_source is 'onedrive_backup_copiado'
        # - file_path contains '.Papelera_Deduplicacion', 'papelera', or '$RECYCLE.BIN'
        cursor = conn.execute("""
            DELETE FROM photos 
            WHERE folder_source IN ('papelera', 'onedrive_backup_copiado')
               OR LOWER(file_path) LIKE '%papelera%'
               OR LOWER(file_path) LIKE '%$recycle.bin%'
               OR LOWER(file_path) LIKE '%recycle.bin%'
        """)
        deleted_trash = cursor.rowcount
        print(f"Registros eliminados (Papelera/Recycle/Backups redundantes): {deleted_trash}")
        
        print("\n--- 2. Deduplicación Estricta por Hash (SHA-256) ---")
        
        # Retrieve all remaining records to perform in-memory scoring and deduplication
        cursor = conn.execute("""
            SELECT id, sha256, folder_source, latitude, longitude, location_name, city, country, file_path 
            FROM photos 
            WHERE sha256 IS NOT NULL AND sha256 != ''
        """)
        rows = cursor.fetchall()
        
        by_hash = {}
        for r in rows:
            rid, sha, source, lat, lng, loc_name, city, country, path = r
            
            has_gps = (lat is not None and lng is not None and lat != 0.0 and lng != 0.0)
            has_loc = bool(loc_name and loc_name.strip())
            has_city = bool(city and city.strip())
            has_country = bool(country and country.strip())
            
            by_hash.setdefault(sha, []).append({
                'id': rid,
                'source': source,
                'has_gps': has_gps,
                'has_loc': has_loc,
                'has_city': has_city,
                'has_country': has_country,
                'path': path
            })
            
        ids_to_keep = set()
        ids_to_delete = []
        duplicate_groups_count = 0
        
        for sha, group in by_hash.items():
            if len(group) == 1:
                ids_to_keep.add(group[0]['id'])
                continue
                
            duplicate_groups_count += 1
            # Score each record in the group
            scored = []
            for item in group:
                score = 0
                if item['has_gps']:
                    score += 1000
                if item['has_loc']:
                    score += 100
                if item['has_city']:
                    score += 50
                if item['has_country']:
                    score += 50
                if item['source'] == 'unified_disk':
                    score += 10
                elif item['source'] == 'F_Organized':
                    score += 5
                
                # We sort by score descending (higher score is better).
                # As tie-breakers, we prefer smaller IDs (older insertions) to maintain insertion history.
                scored.append((score, -item['id'], item['id']))
                
            scored.sort(reverse=True)
            keep_id = scored[0][2]
            ids_to_keep.add(keep_id)
            
            for item in group:
                if item['id'] != keep_id:
                    ids_to_delete.append(item['id'])
                    
        print(f"Grupos de duplicados exactos identificados: {duplicate_groups_count}")
        print(f"Total registros redundantes a eliminar: {len(ids_to_delete)}")
        
        # Execute deletions in chunks to prevent SQLite limit issues or excessive lock holding
        chunk_size = 500
        for i in range(0, len(ids_to_delete), chunk_size):
            chunk = ids_to_delete[i:i+chunk_size]
            conn.execute(
                f"DELETE FROM photos WHERE id IN ({','.join(map(str, chunk))})"
            )
            
        conn.commit()
        print("¡Transacción completada y confirmada con éxito!")
        
        # 3. Reporte de Consolidación
        print("\n=== 3. REPORTE DE CONSOLIDACIÓN ===")
        total_remaining = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        
        with_gps = conn.execute("""
            SELECT COUNT(*) FROM photos 
            WHERE latitude IS NOT NULL 
              AND longitude IS NOT NULL 
              AND latitude != 0.0 
              AND longitude != 0.0
        """).fetchone()[0]
        
        without_gps = total_remaining - with_gps
        
        print(f"Total de fotos restantes en el catálogo: {total_remaining}")
        print(f"  - Con coordenadas GPS válidas:         {with_gps} ({with_gps/total_remaining*100:.2f}%)")
        print(f"  - Sin coordenadas GPS:                {without_gps} ({without_gps/total_remaining*100:.2f}%)")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Ocurrió un fallo crítico: {e}")
        print("La transacción ha sido revertida. No se realizaron cambios permanentes.")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
