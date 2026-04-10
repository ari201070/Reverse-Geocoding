// api/memory-store.js - Spatial Cache Management (Level 1)
import pg from 'pg';
const { Pool } = pg;
import 'dotenv/config';

// 2. Initialize Pool using strictly process.env.DATABASE_URL
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
});

// 3. Error handler for idle clients
pool.on('error', (err) => {
    console.error('[QA WARN] Fallo inesperado en el cliente inactivo de PostGIS:', err.message);
});

/**
 * Gestor de Persistencia de la Lógica de Cascada (Nivel 1 - Caché Local).
 */
class MemoryStore {
    /**
     * 4. Implementación de findMatch(h3Index)
     * Realiza búsqueda exacta por índice H3 en la tabla known_places.
     */
    async findMatch(h3Index) {
        if (!process.env.DATABASE_URL) return null;
        
        try {
            const query = `
                SELECT 
                    google_place_id, 
                    display_name, 
                    place_type, 
                    ST_X(geom) as lng, 
                    ST_Y(geom) as lat 
                FROM known_places 
                WHERE h3_index_res9 = $1 
                LIMIT 1;
            `;
            
            const { rows } = await pool.query(query, [h3Index]);
            
            if (rows.length > 0) {
                return {
                    place_id: rows[0].google_place_id,
                    name: rows[0].display_name,
                    type: rows[0].place_type,
                    lat: rows[0].lat,
                    lng: rows[0].lng,
                    source: 'LOCAL_CACHE_H3'
                };
            }
            return null;
        } catch (error) {
            console.error('[MemoryStore] Error al consultar Caché de Nivel 1:', error.message);
            return null; // Silent fallback to next level in cascade
        }
    }

    /**
     * 5. Implementación de savePlace(placeId, displayName, placeType, lat, lng)
     * Persiste un lugar en la base de datos para futuras resoluciones de Nivel 1.
     */
    async savePlace(placeId, displayName, placeType, lat, lng) {
        if (!process.env.DATABASE_URL || !placeId) return;

        try {
            const query = `
                INSERT INTO known_places (google_place_id, display_name, place_type, geom)
                VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326))
                ON CONFLICT (google_place_id) DO NOTHING;
            `;
            
            // Note: PostGIS ST_MakePoint order is (Longitude, Latitude)
            await pool.query(query, [placeId, displayName, placeType, lng, lat]);
            console.log(`[MemoryStore] Preserving Level 1 Cache: ${displayName}`);
        } catch (error) {
            console.error('[MemoryStore] Fallo al persistir en PostGIS:', error.message);
            // Silent failure: cascade continues but cache is not updated
        }
    }

    // legacy bridge
    async addCluster(item) {
        if (item.lat && item.lng && item.name) {
            // Basic mapping for legacy calls if any
            await this.savePlace(item.place_id || `legacy_${Date.now()}`, item.name, 'point_of_interest', item.lat, item.lng);
        }
    }
}

export default new MemoryStore();
