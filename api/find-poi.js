// api/find-poi.js - Geocoding Cascade Orchestrator (Levels 1, 2, 3)
import 'dotenv/config';
import memoryStore from './memory-store.js';
import * as h3 from 'h3-js';

// Helper for standardized response
function formatResponse(name, address, lat, lng, source, confidence, placeId, isCached) {
    return {
        success: true,
        data: {
            name: name || "Unknown",
            address: address || "Unknown",
            coords: { lat: parseFloat(lat), lng: parseFloat(lng) },
            source: source,
            confidence: confidence,
            place_id: placeId || null
        },
        meta: {
            cached: isCached,
            timestamp: new Date().toISOString()
        }
    };
}

/**
 * POST /api/find-poi
 * Body: { lat, lng, radius }
 */
export default async function handler(req, res) {
    if (req.method && req.method !== 'POST') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    const { latitude, longitude, lat, lng, radius = 500 } = req.body;
    
    // Normalize input
    const targetLat = parseFloat(latitude || lat);
    const targetLng = parseFloat(longitude || lng);

    console.log(`[QA DEBUG] Received Coord: ${targetLat}, ${targetLng}`);

    if (isNaN(targetLat) || isNaN(targetLng)) {
        return res.status(400).json({ success: false, error: 'Invalid coordinates' });
    }

    // --- STEP 0: Rounding & H3 Indexing (v4.0) ---
    const roundedLat = Math.round(targetLat * 10000) / 10000;
    const roundedLng = Math.round(targetLng * 10000) / 10000;
    const h3Index = h3.latLngToCell(roundedLat, roundedLng, 9);
    
    console.log(`[QA DEBUG] H3 Index (Res 9): ${h3Index}`);

    let result = null;

    // --- LEVEL 1: PostGIS/H3 Cache (FREE & FAST) ---
    try {
        if (!process.env.DATABASE_URL) {
            console.warn('[QA WARN] DATABASE_URL no definida. Saltando Nivel 1 (Caché).');
        } else {
            const cachedPlace = await memoryStore.findMatch(h3Index);
            if (cachedPlace) {
                console.log(`[QA] Level 1 Hit (Cache): ${cachedPlace.name}`);
                return res.json(formatResponse(
                    cachedPlace.name, null, targetLat, targetLng, 'LOCAL_CACHE_H3', 1.0, cachedPlace.place_id, true
                ));
            }
        }
    } catch (e) {
        console.warn('[QA] Level 1 Cache Failure:', e.message);
    }

    // --- LEVEL 2: Google Places API New (HIGH PRECISION - NOW PRIMARY FALLBACK) ---
    const GOOGLE_KEY = process.env.GOOGLE_MAPS_API_KEY;
    let googleSuccess = false;
    if (GOOGLE_KEY) {
        try {
            const placesUrl = 'https://places.googleapis.com/v1/places:searchNearby';
            const payload = {
                locationRestriction: {
                    circle: { center: { latitude: targetLat, longitude: targetLng }, radius: radius }
                },
                maxResultCount: 1
            };

            const placesRes = await fetch(placesUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': GOOGLE_KEY,
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.types'
                },
                body: JSON.stringify(payload)
            });

            if (placesRes.ok) {
                const data = await placesRes.json();
                const place = data.places?.[0];

                if (place && place.displayName?.text) {
                    const name = place.displayName.text;
                    const address = place.formattedAddress;
                    const resultId = place.id;
                    const type = place.types?.[0] || 'establishment';

                    // PERSISTENCE (v4.0)
                    await memoryStore.savePlace(resultId, name, type, targetLat, targetLng);
                    googleSuccess = true;

                    return res.json(formatResponse(
                        name, address, targetLat, targetLng, 'GOOGLE_PLACES_NEW', 0.99, resultId, false
                    ));
                }
            }
        } catch (e) {
            console.error('[QA] Level 2 Google Places Failure:', e.message);
        }
    }

    // --- LEVEL 3: OpenCage Fallback (ECONOMICAL - SECONDARY) ---
    const OPENCAGE_KEY = process.env.OPENCAGE_API_KEY || process.env.VITE_OPENCAGE_API_KEY;
    if (!googleSuccess && OPENCAGE_KEY) {
        try {
            const ocRes = await fetch(`https://api.opencagedata.com/geocode/v1/json?q=${roundedLat},${roundedLng}&key=${OPENCAGE_KEY}&language=es&no_annotations=1&no_record=true`);
            if (ocRes.ok) {
                const ocData = await ocRes.json();
                if (ocData.results && ocData.results.length > 0) {
                    const best = ocData.results[0];
                    const ocConfidence = (best.confidence || 0) / 10;
                    
                    const name = best.components.tourism || best.components.landscape || best.components.pedestrian || best.formatted;

                    // WARNING: If it returns "Münster", it's likely a sandbox/tier issue
                    if (name.includes("Münster")) {
                        console.warn('[QA] OpenCage returned Münster. Ignoring as likely sandbox limitation.');
                    } else {
                        // PERSISTENCE (v4.0)
                        await memoryStore.savePlace('oc_' + (best.annotations?.MGRS || Date.now()), name, 'point_of_interest', targetLat, targetLng);
                        
                        return res.json(formatResponse(
                            name, best.formatted, targetLat, targetLng, 'OPENCAGE', ocConfidence, null, false
                        ));
                    }
                }
            }
        } catch (e) {
            console.warn('[QA] Level 3 OpenCage Failure:', e.message);
        }
    }

    // --- FINAL FALLBACK: Coordinates Only ---
    return res.json(formatResponse(
        `${roundedLat}, ${roundedLng}`, "Coordenadas puras (Sin resultados)", targetLat, targetLng, 'COORDINATES_ONLY', 0.1, null, false
    ));
}
