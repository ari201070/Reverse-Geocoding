// api/memory-store.js - Spatial Cache Management (Level 1)
import pg from 'pg';
const { Pool } = pg;
import 'dotenv/config';

// Initialize Pool using strictly process.env.DATABASE_URL
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
});

pool.on('error', (err) => {
    console.error('[QA WARN] Fallo inesperado en el cliente inactivo de PostGIS:', err.message);
});

/**
 * Gestor de Persistencia de la Lógica de Cascada (Nivel 1 - Caché Local).
 * Implementa la Soberanía de Datos mediante índices H3 y redondeo de privacidad.
 */
class MemoryStore {
    /**
     * Persiste un lugar en la base de datos siguiendo el estándar de Soberanía de Datos.
     * Aplica redondeo a 4 decimales y guarda la evidencia del ancla.
     */
    async savePlace(placeId, name, placeType, lat, lng, anchorData = null) {
        if (!process.env.DATABASE_URL || !placeId) return;

        try {
            const anonLat = Math.round(lat * 10000) / 10000;
            const anonLng = Math.round(lng * 10000) / 10000;
            
            const h3 = require('h3-js');
            const h3Index = h3.latLngToCell(anonLat, anonLng, 9);

            const query = `
                INSERT INTO known_places (name, place_id, anon_latitude, anon_longitude, h3_res9, anchor_evidence, anchor_method)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (place_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    anchor_evidence = COALESCE(known_places.anchor_evidence, EXCLUDED.anchor_evidence),
                    anchor_method = COALESCE(known_places.anchor_method, EXCLUDED.anchor_method),
                    created_at = NOW();
            `;
            
            await pool.query(query, [
                name, 
                placeId, 
                anonLat, 
                anonLng, 
                h3Index, 
                anchorData ? JSON.stringify(anchorData) : null,
                anchorData ? anchorData.method : null
            ]);
            console.log(`[MemoryStore] Preserving Sovereign Data: ${name} @ ${h3Index}`);
        } catch (error) {
            console.error('[MemoryStore] Fallo al persistir en PostGIS:', error.message);
        }
    }

    /**
     * Búsqueda ultra rápida mediante índice B-Tree sobre H3.
     * Retorna el lugar y la evidencia del ancla para validación.
     */
    async findMatch(h3Index) {
        if (!process.env.DATABASE_URL) return null;
        
        try {
            const query = `
                SELECT 
                    place_id, 
                    name as display_name, 
                    'point_of_interest' as place_type, 
                    anon_longitude as lng, 
                    anon_latitude as lat,
                    anchor_evidence,
                    anchor_method
                FROM known_places 
                WHERE h3_res9 = $1 
                LIMIT 1;
            `;
            
            const { rows } = await pool.query(query, [h3Index]);
            
            if (rows.length > 0) {
                return {
                    place_id: rows[0].place_id,
                    name: rows[0].display_name,
                    type: rows[0].place_type,
                    lat: rows[0].lat,
                    lng: rows[0].lng,
                    source: 'LOCAL_CACHE_H3',
                    anchor: {
                        evidence: rows[0].anchor_evidence,
                        method: rows[0].anchor_method
                    }
                };
            }
            return null;
        } catch (error) {
            console.error('[MemoryStore] Error al consultar Caché de Nivel 1:', error.message);
            return null;
        }
    }

    /**
     * Gestión de Caché de Resultados de Consenso (Lotes)
     */
    async findClusterResult(clusterHash) {
        if (!process.env.DATABASE_URL) return null;
        try {
            const query = `SELECT result_json FROM cluster_results WHERE cluster_hash = $1 LIMIT 1;`;
            const { rows } = await pool.query(query, [clusterHash]);
            return rows.length > 0 ? rows[0].result_json : null;
        } catch (e) {
            console.error('[MemoryStore] Error buscando caché de clúster:', e.message);
            return null;
        }
    }

    async saveClusterResult(clusterHash, result) {
        if (!process.env.DATABASE_URL) return;
        try {
            await pool.query(`
                CREATE TABLE IF NOT EXISTS cluster_results (
                    cluster_hash TEXT PRIMARY KEY,
                    result_json JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            `);
            const query = `
                INSERT INTO cluster_results (cluster_hash, result_json)
                VALUES ($1, $2)
                ON CONFLICT (cluster_hash) DO UPDATE SET result_json = EXCLUDED.result_json, created_at = NOW();
            `;
            await pool.query(query, [clusterHash, JSON.stringify(result)]);
        } catch (e) {
            console.error('[MemoryStore] Error guardando caché de clúster:', e.message);
        }
    }

    // legacy bridge
    async addCluster(item) {
        if (item.lat && item.lng && item.name) {
            await this.savePlace(item.place_id || `legacy_${Date.now()}`, item.name, 'point_of_interest', item.lat, item.lng);
        }
    }
}

export default new MemoryStore();
