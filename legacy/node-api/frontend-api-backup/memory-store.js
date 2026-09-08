// api/memory-store.js - Spatial Cache Management (Level 1)
import pg from 'pg';
const { Pool } = pg;
import 'dotenv/config';
import * as h3 from 'h3-js';
import fs from 'fs';
import path from 'path';

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
     * Si se pasan lat, lng y heading, realiza la desambiguación por Vector de Visión usando PostGIS.
     */
    async findMatch(h3Index, lat = null, lng = null, heading = null) {
        if (!process.env.DATABASE_URL) return null;
        
        try {
            let query = '';
            let params = [];

            if (lat !== null && lng !== null && heading !== null) {
                query = `
                    SELECT 
                        place_id, 
                        name as display_name, 
                        'point_of_interest' as place_type, 
                        anon_longitude as lng, 
                        anon_latitude as lat,
                        anchor_evidence,
                        anchor_method,
                        COALESCE(confidence_score, 1.0) * fn_calculate_vision_multiplier(
                            ST_SetSRID(ST_MakePoint($2, $3), 4326),
                            geom,
                            $4
                        ) as adjusted_confidence
                    FROM known_places 
                    WHERE h3_res9 = $1 
                    ORDER BY adjusted_confidence DESC, COALESCE(confidence_score, 1.0) DESC
                    LIMIT 1;
                `;
                params = [h3Index, parseFloat(lng), parseFloat(lat), parseFloat(heading)];
            } else {
                query = `
                    SELECT 
                        place_id, 
                        name as display_name, 
                        'point_of_interest' as place_type, 
                        anon_longitude as lng, 
                        anon_latitude as lat,
                        anchor_evidence,
                        anchor_method,
                        COALESCE(confidence_score, 1.0) as adjusted_confidence
                    FROM known_places 
                    WHERE h3_res9 = $1 
                    ORDER BY COALESCE(confidence_score, 1.0) DESC
                    LIMIT 1;
                `;
                params = [h3Index];
            }
            
            const { rows } = await pool.query(query, params);
            
            if (rows.length > 0) {
                return {
                    place_id: rows[0].place_id,
                    name: rows[0].display_name,
                    type: rows[0].place_type,
                    lat: rows[0].lat,
                    lng: rows[0].lng,
                    source: 'LOCAL_CACHE_H3',
                    confidence: parseFloat(rows[0].adjusted_confidence) || 1.0,
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
     * Búsqueda por Radio Espacial Local (Nivel 1.5 - PostGIS).
     * Encuentra hitos conocidos dentro de un radio en metros utilizando funciones geográficas de PostGIS.
     * Esto proporciona un fallback gratuito de alta calidad si las APIs de Google están desactivadas.
     */
    async findNearby(lat, lng, radiusMeters = 50) {
        if (!process.env.DATABASE_URL) return null;
        try {
            const query = `
                SELECT 
                    place_id, 
                    name as display_name, 
                    'point_of_interest' as place_type, 
                    anon_longitude as lng, 
                    anon_latitude as lat, 
                    COALESCE(confidence_score, 1.0) as confidence,
                    ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography) as distance_meters
                FROM known_places
                WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography, $3)
                ORDER BY distance_meters ASC, COALESCE(confidence_score, 1.0) DESC
                LIMIT 1;
            `;
            const { rows } = await pool.query(query, [parseFloat(lng), parseFloat(lat), parseFloat(radiusMeters)]);
            
            if (rows.length > 0) {
                console.log(`[MemoryStore] Level 1.5 Hit (Spatial Radius DB): ${rows[0].display_name} (${Math.round(rows[0].distance_meters)}m away)`);
                return {
                    place_id: rows[0].place_id,
                    name: rows[0].display_name,
                    type: rows[0].place_type,
                    lat: parseFloat(rows[0].lat),
                    lng: parseFloat(rows[0].lng),
                    source: 'LOCAL_SPATIAL_RADIUS_DB',
                    confidence: parseFloat(rows[0].confidence),
                    distance_meters: parseFloat(rows[0].distance_meters)
                };
            }
            return null;
        } catch (error) {
            console.error('[MemoryStore] Error en búsqueda de radio espacial local:', error.message);
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
            // Recuperar datos originales para el Bucle de Re-aprendizaje antes de la actualización
            let originalPlace = null;
            try {
                const selectRes = await pool.query(
                    `SELECT name, anon_latitude, anon_longitude, h3_res9 FROM known_places WHERE id = $1`,
                    [id]
                );
                if (selectRes.rows.length > 0) {
                    originalPlace = selectRes.rows[0];
                }
            } catch (err) {
                console.warn('[MemoryStore] No se pudo recuperar el registro original para la memoria:', err.message);
            }

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

            // Si la actualización es exitosa, escribir lección en MEMORY.md (Bucle de Re-aprendizaje)
            if (res.rowCount > 0 && originalPlace) {
                try {
                    const h3Cell = originalPlace.h3_res9 || (originalPlace.anon_latitude && originalPlace.anon_longitude ? h3.latLngToCell(originalPlace.anon_latitude, originalPlace.anon_longitude, 9) : 'Desconocida');
                    const initialHypothesis = originalPlace.name || 'Desconocido';
                    let humanCorrection = '';
                    let reason = '';

                    if (action === 'APPROVE') {
                        humanCorrection = 'Aprobado sin cambios';
                        reason = 'El operador confirmó que la hipótesis de la IA es correcta.';
                    } else if (action === 'REJECT') {
                        humanCorrection = 'Rechazado';
                        reason = 'El operador marcó el registro propuesto como incorrecto o inválido.';
                    } else if (action === 'EDIT') {
                        humanCorrection = `Editado a: "${correctedData.name}" (${correctedData.lat}, ${correctedData.lng})`;
                        reason = 'El operador corrigió manualmente el nombre o las coordenadas GPS.';
                    }

                    const timestamp = new Date().toISOString();
                    const lessonBlock = `\n## Lección: ${timestamp} - Conflicto en Celda ${h3Cell}\n- **Contexto Inicial:** ${initialHypothesis}\n- **Corrección Humana:** ${humanCorrection}\n- **Razón del Escalamiento:** ${reason}\n- **Acción Sugerida:** En futuros análisis de esta celda, priorizar ${humanCorrection} sobre el GPS crudo.\n---\n`;
                    
                    const memoryFilePath = path.join(process.cwd(), 'MEMORY.md');
                    await fs.promises.appendFile(memoryFilePath, lessonBlock, 'utf8');
                    console.log(`[MemoryStore] Lección de re-aprendizaje guardada exitosamente en MEMORY.md para celda ${h3Cell}`);
                } catch (memErr) {
                    console.error('[MemoryStore] Error al guardar lección en MEMORY.md:', memErr.message);
                }
            }

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

    /**
     * Seeda la base de datos local pre-cargando hitos culturales claves si está vacía.
     * Garantiza operatividad offline-first robusta.
     */
    async seedKnownPlacesIfEmpty() {
        if (!process.env.DATABASE_URL) return;
        try {
            // Verificar si la tabla existe y cuántos registros tiene
            const checkQuery = `SELECT COUNT(*) FROM known_places;`;
            const { rows } = await pool.query(checkQuery);
            const count = parseInt(rows[0].count, 10);
            
            if (count === 0) {
                console.log('[MemoryStore] Spatial Cache is empty. Seeding key landmarks...');
                
                // Catedral Basílica de Nuestra Señora del Rosario
                await this.savePlace(
                    'catedral_rosario_local',
                    'Catedral Basílica de Nuestra Señora del Rosario',
                    'point_of_interest',
                    -32.9468,
                    -60.6385,
                    { method: 'LANDMARK', source: 'OFFLINE_SEED' },
                    1.00,
                    { reason: 'Auto-sembrado offline hito principal Rosario' },
                    'RECONSTRUCTED'
                );

                // Monumento Histórico Nacional a la Bandera
                await this.savePlace(
                    'monumento_bandera_local',
                    'Monumento Histórico Nacional a la Bandera',
                    'point_of_interest',
                    -32.9472,
                    -60.6304,
                    { method: 'LANDMARK', source: 'OFFLINE_SEED' },
                    1.00,
                    { reason: 'Auto-sembrado offline hito principal Rosario' },
                    'RECONSTRUCTED'
                );

                // Casita de Té en el Bosque de Arrayanes
                await this.savePlace(
                    'casita_te_bariloche_local',
                    'Casita de Té en el Bosque de Arrayanes',
                    'point_of_interest',
                    -40.7820,
                    -71.6433,
                    { method: 'LANDMARK', source: 'OFFLINE_SEED' },
                    1.00,
                    { reason: 'Auto-sembrado offline hito principal Bariloche' },
                    'RECONSTRUCTED'
                );
                
                console.log('[MemoryStore] Key landmarks seeded successfully.');
            } else {
                console.log(`[MemoryStore] Spatial Cache already contains ${count} places. Seeding bypassed.`);
            }
        } catch (error) {
            console.error('[MemoryStore] Failed to seed spatial cache (this is normal if table not yet initialized):', error.message);
        }
    }
}

const store = new MemoryStore();
if (process.env.DATABASE_URL) {
    store.seedKnownPlacesIfEmpty().catch(err => {
        console.error('[MemoryStore] Auto-seeding error:', err.message);
    });
}

export default store;
