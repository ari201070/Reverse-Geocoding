// api/memory-store.js - Spatial Cache Management (Level 1)
import pg from 'pg';
const { Pool } = pg;
import 'dotenv/config';
import * as h3 from 'h3-js';

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
    async savePlace(placeId, name, placeType, lat, lng, anchorData = null, confidenceScore = null, metadataEvidence = null, reviewStatus = 'RECONSTRUCTED') {
        if (!process.env.DATABASE_URL || !placeId) return;

        try {
            const anonLat = Math.round(lat * 10000) / 10000;
            const anonLng = Math.round(lng * 10000) / 10000;
            
            const h3Index = h3.latLngToCell(anonLat, anonLng, 9);

            const query = `
                INSERT INTO known_places (
                    name, place_id, anon_latitude, anon_longitude, h3_res9, 
                    anchor_evidence, anchor_method, confidence_score, metadata_evidence, review_status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (place_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    anchor_evidence = COALESCE(known_places.anchor_evidence, EXCLUDED.anchor_evidence),
                    anchor_method = COALESCE(known_places.anchor_method, EXCLUDED.anchor_method),
                    confidence_score = EXCLUDED.confidence_score,
                    metadata_evidence = EXCLUDED.metadata_evidence,
                    review_status = EXCLUDED.review_status,
                    created_at = NOW();
            `;
            
            await pool.query(query, [
                name, 
                placeId, 
                anonLat, 
                anonLng, 
                h3Index, 
                anchorData ? JSON.stringify(anchorData) : null,
                anchorData ? anchorData.method : null,
                confidenceScore,
                metadataEvidence ? JSON.stringify(metadataEvidence) : null,
                reviewStatus
            ]);
            console.log(`[MemoryStore] Preserving Sovereign Data: ${name} @ ${h3Index} with status ${reviewStatus}`);
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

    /**
     * Trae todos los registros con estado 'PENDING_REVIEW' para la cola de auditoría (HITL).
     */
    async getPendingReviews() {
        if (!process.env.DATABASE_URL) return [];
        try {
            const query = `
                SELECT 
                    id, name, place_id, anon_latitude as lat, anon_longitude as lng, 
                    h3_res9, anchor_evidence, confidence_score, metadata_evidence, review_status, created_at
                FROM known_places
                WHERE review_status = 'PENDING_REVIEW'
                ORDER BY created_at DESC;
            `;
            const { rows } = await pool.query(query);
            return rows;
        } catch (error) {
            console.error('[MemoryStore] Fallo al obtener revisiones pendientes:', error.message);
            return [];
        }
    }

    /**
     * Resuelve una revisión pendiente en PostGIS.
     * Acciones: 'APPROVE' (pasa a RECONSTRUCTED), 'REJECT' (pasa a REJECTED), o 'EDIT' (permite corregir datos y pasa a RECONSTRUCTED).
     */
    async resolveReview(id, action, correctedData = {}) {
        if (!process.env.DATABASE_URL) return false;
        try {
            let query = '';
            let params = [];

            if (action === 'APPROVE') {
                query = `
                    UPDATE known_places 
                    SET review_status = 'RECONSTRUCTED', confidence_score = 1.00
                    WHERE id = $1;
                `;
                params = [id];
            } else if (action === 'REJECT') {
                query = `
                    UPDATE known_places 
                    SET review_status = 'REJECTED', confidence_score = 0.00
                    WHERE id = $1;
                `;
                params = [id];
            } else if (action === 'EDIT') {
                const name = correctedData.name || '';
                const lat = parseFloat(correctedData.lat);
                const lng = parseFloat(correctedData.lng);

                if (!name || isNaN(lat) || isNaN(lng)) {
                    throw new Error('Datos incorrectos para edición');
                }

                const anonLat = Math.round(lat * 10000) / 10000;
                const anonLng = Math.round(lng * 10000) / 10000;
                const h3Index = h3.latLngToCell(anonLat, anonLng, 9);

                query = `
                    UPDATE known_places 
                    SET name = $2, 
                        anon_latitude = $3, 
                        anon_longitude = $4, 
                        h3_res9 = $5,
                        review_status = 'RECONSTRUCTED',
                        confidence_score = 1.00,
                        metadata_evidence = jsonb_set(
                            COALESCE(metadata_evidence, '{}'::jsonb), 
                            '{human_correction}', 
                            '"Editado y aprobado por operador"'
                        )
                    WHERE id = $1;
                `;
                params = [id, name, anonLat, anonLng, h3Index];
            } else {
                throw new Error(`Acción desconocida: ${action}`);
            }

            const res = await pool.query(query, params);
            return res.rowCount > 0;
        } catch (error) {
            console.error('[MemoryStore] Fallo al resolver revisión:', error.message);
            return false;
        }
    }

    /**
     * Guarda una foto ancla en PostGIS para el Pilar 7.
     */
    async saveAnchorPhoto(lat, lng, timestampUtc, visualSignature = null) {
        if (!process.env.DATABASE_URL) return null;
        try {
            const anonLat = Math.round(lat * 10000) / 10000;
            const anonLng = Math.round(lng * 10000) / 10000;
            const h3Index = h3.latLngToCell(anonLat, anonLng, 9);

            const query = `
                INSERT INTO anchor_photos (lat, lng, h3_res9, timestamp_utc, visual_signature)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id;
            `;
            const { rows } = await pool.query(query, [
                anonLat, 
                anonLng, 
                h3Index, 
                new Date(timestampUtc), 
                visualSignature ? JSON.stringify(visualSignature) : null
            ]);
            return rows[0].id;
        } catch (error) {
            console.error('[MemoryStore] Fallo al guardar foto ancla:', error.message);
            return null;
        }
    }

    /**
     * Busca una foto ancla reciente dentro de los 15 minutos y en la misma celda H3.
     */
    async findRecentAnchorPhoto(lat, lng, timestampUtc) {
        if (!process.env.DATABASE_URL) return null;
        try {
            const anonLat = Math.round(lat * 10000) / 10000;
            const anonLng = Math.round(lng * 10000) / 10000;
            const h3Index = h3.latLngToCell(anonLat, anonLng, 9);

            const query = `
                SELECT id, lat, lng, timestamp_utc, visual_signature
                FROM anchor_photos
                WHERE h3_res9 = $1
                  AND timestamp_utc >= $2::timestamp - INTERVAL '15 minutes'
                  AND timestamp_utc <= $2::timestamp + INTERVAL '15 minutes'
                ORDER BY ABS(EXTRACT(EPOCH FROM (timestamp_utc - $2::timestamp))) ASC
                LIMIT 1;
            `;
            const { rows } = await pool.query(query, [h3Index, new Date(timestampUtc)]);
            if (rows.length > 0) {
                return {
                    id: rows[0].id,
                    lat: parseFloat(rows[0].lat),
                    lng: parseFloat(rows[0].lng),
                    timestamp_utc: rows[0].timestamp_utc,
                    visual_signature: rows[0].visual_signature,
                    source: 'ANCHOR_PHOTO'
                };
            }
            return null;
        } catch (error) {
            console.error('[MemoryStore] Fallo al buscar foto ancla reciente:', error.message);
            return null;
        }
    }
}

export default new MemoryStore();
