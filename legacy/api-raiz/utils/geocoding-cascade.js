import 'dotenv/config';
import memoryStore from '../memory-store.js';
import * as h3 from 'h3-js';
import { contextualizeLandmarkName } from './landmark-context.js';

export async function performGeocodingCascade(lat, lng, radius = 50, keywords = "") {
    const roundedLat = Math.round(lat * 10000) / 10000;
    const roundedLng = Math.round(lng * 10000) / 10000;
    const h3Index = h3.latLngToCell(roundedLat, roundedLng, 9);

    // LEVEL 1: Cache
    try {
        const cachedPlace = await memoryStore.findMatch(h3Index);
        if (cachedPlace) {
            return { 
                name: cachedPlace.name, 
                address: null, 
                source: 'LOCAL_CACHE_H3', 
                confidence: 1.0, 
                place_id: cachedPlace.place_id, 
                cached: true 
            };
        }
    } catch (e) { console.warn('[Cascade] L1 Cache Failure:', e.message); }

    // LEVEL 2: Google Places API New
    const GOOGLE_KEY = process.env.GOOGLE_CLOUD_API_KEY || process.env.GOOGLE_MAPS_API_KEY;
    const DISABLE_PAID_GOOGLE_APIS = process.env.DISABLE_PAID_GOOGLE_APIS === 'true';
    if (DISABLE_PAID_GOOGLE_APIS) {
        console.log(`[Cascade INFO] Paid Google APIs are disabled. Bypassing Google Places (Level 2). Trying Level 1.5 (Local Radius search)...`);
        try {
            const nearbyLocalPlace = await memoryStore.findNearby(lat, lng, radius);
            if (nearbyLocalPlace) {
                return { 
                    name: nearbyLocalPlace.name, 
                    address: null, 
                    source: 'LOCAL_SPATIAL_RADIUS_DB', 
                    confidence: nearbyLocalPlace.confidence || 0.95, 
                    place_id: nearbyLocalPlace.place_id, 
                    cached: true 
                };
            }
        } catch (e) {
            console.warn('[Cascade] Level 1.5 Spatial Radius Failure:', e.message);
        }
    } else if (GOOGLE_KEY) {
        try {
            const placesUrl = 'https://places.googleapis.com/v1/places:searchNearby';
            const payload = {
                locationRestriction: {
                    circle: { center: { latitude: lat, longitude: lng }, radius: radius }
                },
                maxResultCount: 1
            };

            const placesRes = await fetch(placesUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': GOOGLE_KEY,
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.types',
                    'X-Goog-Language-Code': 'es'
                },
                body: JSON.stringify(payload)
            });

            if (placesRes.ok) {
                const data = await placesRes.json();
                const place = data.places?.[0];
                if (place && place.displayName?.text) {
                    let name = place.displayName.text;
                    const address = place.formattedAddress;
                    const resultId = place.id;
                    const type = place.types?.[0] || 'establishment';
                    
                    // Aplicar desambiguación y contextualización de hitos genéricos
                    name = contextualizeLandmarkName(name, address, lat, lng);

                    await memoryStore.savePlace(resultId, name, type, lat, lng);
                    return { 
                        name, address, source: 'GOOGLE_PLACES_NEW', 
                        confidence: 0.99, place_id: resultId, cached: false 
                    };
                }
            }
        } catch (e) { console.error('[Cascade] L2 Google Failure:', e.message); }
    }

    // LEVEL 3: OpenCage
    const OPENCAGE_KEY = process.env.OPENCAGE_API_KEY || process.env.VITE_OPENCAGE_API_KEY;
    if (OPENCAGE_KEY) {
        try {
            const ocRes = await fetch(`https://api.opencagedata.com/geocode/v1/json?q=${roundedLat},${roundedLng}&key=${OPENCAGE_KEY}&language=es&no_annotations=1&no_record=true`);
            if (ocRes.ok) {
                const ocData = await ocRes.json();
                if (ocData.results && ocData.results.length > 0) {
                    const best = ocData.results[0];
                    const ocConfidence = (best.confidence || 0) / 10;
                    const name = best.components.tourism || best.components.landscape || best.components.pedestrian || best.formatted;
                    if (!name?.includes("Münster")) {
                        await memoryStore.savePlace('oc_' + (best.annotations?.MGRS || Date.now()), name, 'point_of_interest', lat, lng);
                        return { 
                            name, address: best.formatted, source: 'OPENCAGE', 
                            confidence: ocConfidence, place_id: null, cached: false 
                        };
                    }
                }
            }
        } catch (e) { console.warn('[Cascade] L3 OpenCage Failure:', e.message); }
    }

    return { 
        name: `${roundedLat}, ${roundedLng}`, 
        address: "Coordenadas puras (Sin resultados)", 
        source: 'COORDINATES_ONLY', 
        confidence: 0.1, 
        place_id: null, 
        cached: false 
    };
}
