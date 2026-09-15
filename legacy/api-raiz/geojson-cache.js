// api/geojson-cache.js
// Endpoint para servir la caché espacial soberana de países y la caché local de PostGIS (known_places)
// como una FeatureCollection GeoJSON unificada.
import pg from 'pg';
const { Pool } = pg;
import 'dotenv/config';
import { loadWorldGeoJson } from './utils/spatial-utils.js';

let pool = null;
if (process.env.DATABASE_URL) {
    pool = new Pool({
        connectionString: process.env.DATABASE_URL,
        max: 10,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
    });
}

export default async function handler(req, res) {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.status(204).send('');
        return;
    }

    if (req.method !== 'GET') {
        res.status(405).json({ error: 'Method Not Allowed' });
        return;
    }

    try {
        const { bbox } = req.query;
        let countryFeatures = [];

        // 1. Cargar y filtrar el mapa GeoJSON de países localmente
        const worldGeoJson = loadWorldGeoJson();
        if (worldGeoJson && worldGeoJson.features) {
            if (bbox) {
                // Parsear bbox: minLng,minLat,maxLng,maxLat
                const [minLng, minLat, maxLng, maxLat] = bbox.split(',').map(parseFloat);
                
                if (!isNaN(minLng) && !isNaN(minLat) && !isNaN(maxLng) && !isNaN(maxLat)) {
                    // Filtrar países cuyas cajas delimitadoras intersectan el bbox actual del mapa
                    countryFeatures = worldGeoJson.features.filter(feature => {
                        if (!feature.bbox) return true; // Si no tiene bbox por alguna razón, incluirlo
                        const [fMinLng, fMinLat, fMaxLng, fMaxLat] = feature.bbox;
                        
                        // Chequeo de intersección de rectángulos BBOX
                        const intersects = !(
                            fMinLng > maxLng ||
                            fMaxLng < minLng ||
                            fMinLat > maxLat ||
                            fMaxLat < minLat
                        );
                        return intersects;
                    }).map(feature => {
                        // Inyectar un identificador de origen para Leaflet
                        return {
                            ...feature,
                            properties: {
                                ...feature.properties,
                                source: 'LOCAL_COUNTRY_BOUNDARIES'
                            }
                        };
                    });
                } else {
                    countryFeatures = worldGeoJson.features;
                }
            } else {
                // Si no se pide bbox, retornar todos los países (para carga inicial global)
                countryFeatures = worldGeoJson.features;
            }
        }

        let databaseFeatures = [];

        // 2. Si hay base de datos, mezclar los puntos espaciales aprobados de known_places
        if (pool) {
            try {
                const query = `
                    SELECT 
                        place_id, 
                        name, 
                        anon_latitude, 
                        anon_longitude,
                        confidence_score,
                        h3_res9,
                        place_data
                    FROM known_places
                    WHERE review_status = 'RECONSTRUCTED'
                    ORDER BY created_at DESC;
                `;
                const { rows } = await pool.query(query);
                
                databaseFeatures = rows.map(row => {
                    if (row.place_data && row.place_data.type === 'Feature') {
                        return row.place_data;
                    }
                    return {
                        type: 'Feature',
                        id: row.place_id,
                        geometry: {
                            type: 'Point',
                            coordinates: [parseFloat(row.anon_longitude), parseFloat(row.anon_latitude)]
                        },
                        properties: {
                            place_id: row.place_id,
                            name: row.name,
                            confidence: parseFloat(row.confidence_score) || 1.0,
                            h3_index: row.h3_res9,
                            source: 'LOCAL_CACHE_POSTGIS'
                        }
                    };
                });
            } catch (dbErr) {
                console.warn('[GeoJSON Cache] Falló consulta a DB, sirviendo solo mapa de países:', dbErr.message);
            }
        }

        // Combinar capas (puntos de DB + polígonos de países visibles)
        const combinedFeatures = [...databaseFeatures, ...countryFeatures];

        console.log(`[GeoJSON Cache] Sirviendo con éxito ${countryFeatures.length} límites de países y ${databaseFeatures.length} puntos locales.`);
        
        res.status(200).json({
            type: 'FeatureCollection',
            features: combinedFeatures
        });
    } catch (error) {
        console.error('[GeoJSON Cache] Error general en handler:', error.message);
        res.status(500).json({ error: 'Fallo al recuperar la caché espacial GeoJSON unificada' });
    }
}
