// api/find-poi.js - Real Google Places API (New), OpenCage, and Vision integration cascade
// Incorporates proper response format and environment variables

require('dotenv').config();
const memoryStore = require('./memory-store');

// Helper for standard response
function formatResponse(name, address, lat, lng, source, confidence, placeId, isCached, timestamp) {
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
            timestamp: new Date(timestamp || Date.now()).toISOString()
        }
    };
}

/**
 * Filters out generic/noise names from API results.
 */
function isGenericName(name) {
    if (!name) return true;
    const GENERIC_PATTERNS = [
        /^calle\s/i, /^avenida\s/i, /^av\.\s/i, /^ruta\s/i,
        /^\d+$/, /^ruta nacional/i, /^autopista/i,
        /\d{2}\/\d{2}/, // dates
    ];
    return GENERIC_PATTERNS.some(p => p.test(name.trim()));
}

/**
 * POST /api/find-poi
 * Body: { lat, lng, timestamp, keywords, landmarkFromVision, radius }
 */
module.exports = async (req, res) => {
    if (req.method && req.method !== 'POST') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    const { lat, lng, timestamp, keywords, landmarkFromVision, radius = 500 } = req.body;
    const sanitize = (val) => typeof val === 'string' ? val.replace(/'/g, "''") : val;

    if (!lat || !lng) {
        return res.status(400).json({ success: false, error: 'lat and lng are required' });
    }

    const GOOGLE_API_KEY = process.env.GOOGLE_MAPS_API_KEY;
    const OPENCAGE_API_KEY = process.env.VITE_OPENCAGE_API_KEY || process.env.OPENCAGE_API_KEY;

    // 1. Check Spatial Memory first (fast, free)
    const remembered = memoryStore.findMatch(lat, lng, timestamp);
    if (remembered) {
        return res.json(formatResponse(
            remembered.name, remembered.address, remembered.lat, remembered.lng,
            'SPATIAL_MEMORY', 1.0, remembered.place_id, true, remembered.timestamp
        ));
    }

    let bestName = null;
    let bestAddress = null;
    let bestSource = null;
    let bestConfidence = 0;
    let bestPlaceId = null;

    // 2. OpenCage Geocoding (economical fallback for address/basic location)
    if (OPENCAGE_API_KEY) {
        try {
            // Important: OpenCage recommends explicit lat/lng or proper URL encoding.
            // Using precise URL encoding `q=lat%2Clng` (+ is space in URLs, so don't use it)
            const queryRaw = `${lat},${lng}`;
            const opencageUrl = `https://api.opencagedata.com/geocode/v1/json?q=${encodeURIComponent(queryRaw)}&key=${OPENCAGE_API_KEY}`;
            const ocRes = await fetch(opencageUrl);
            if (ocRes.ok) {
                const ocData = await ocRes.json();
                if (ocData.results && ocData.results.length > 0) {
                    const best = ocData.results[0];
                    bestAddress = best.formatted;
                    bestName = best.components.tourism || best.components.pedestrian || best.components.road || "Ubicación genérica";
                    bestSource = 'OPENCAGE';
                    bestConfidence = (best.confidence || 0) / 10;
                }
            }
        } catch (err) {
            console.error('OpenCage API error:', err.message);
        }
    }

    // 3. Google Places (New) - High precision semantic data
    if (GOOGLE_API_KEY) {
        try {
            const searchKeyword = landmarkFromVision || keywords || '';
            const placesUrl = 'https://places.googleapis.com/v1/places:searchNearby';
            const payload = {
                includedTypes: ['tourist_attraction', 'museum', 'park', 'landmark', 'establishment'],
                maxResultCount: 5,
                locationRestriction: {
                    circle: { center: { latitude: parseFloat(lat), longitude: parseFloat(lng) }, radius: radius }
                }
            };

            if (searchKeyword) payload.rankPreference = 'RELEVANCE';

            const placesRes = await fetch(placesUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.types,places.id',
                    'X-Goog-Api-Key': GOOGLE_API_KEY
                },
                body: JSON.stringify(payload)
            });

            if (placesRes.ok) {
                const data = await placesRes.json();
                const places = data.places || [];

                if (places.length > 0) {
                    const PRIORITY = { tourist_attraction: 120, museum: 110, park: 100, landmark: 90, point_of_interest: 80, establishment: 50 };
                    
                    const best = places
                        .filter(p => !isGenericName(p.displayName?.text))
                        .sort((a, b) => {
                            const scoreA = Math.max(...(a.types || []).map(t => PRIORITY[t] || 10));
                            const scoreB = Math.max(...(b.types || []).map(t => PRIORITY[t] || 10));
                            return scoreB - scoreA;
                        })[0] || places[0];
                    
                    if (best && best.displayName?.text) {
                        bestName = sanitize(best.displayName.text);
                        bestAddress = best.formattedAddress || bestAddress;
                        bestPlaceId = best.id;
                        bestSource = 'GOOGLE_PLACES_NEW';
                        bestConfidence = 0.95; // Google places is very confident
                    }
                }
            }
        } catch (err) {
            console.error('Google Places API error:', err.message);
        }
    }

    // 4. Vision API priority (if a landmark was extracted via Vision previously, use it if Google failed to find something better)
    if (landmarkFromVision && bestSource !== 'GOOGLE_PLACES_NEW') {
        bestName = sanitize(landmarkFromVision);
        bestSource = 'VISION_API';
        bestConfidence = 0.90;
    }

    // Send final result back
    if (bestName && bestSource) {
        const resultItem = {
            name: bestName,
            address: bestAddress,
            lat, lng,
            timestamp: timestamp || Date.now(),
            place_id: bestPlaceId
        };
        memoryStore.addCluster(resultItem);

        return res.json(formatResponse(
            bestName, bestAddress, lat, lng, bestSource, bestConfidence, bestPlaceId, false, timestamp
        ));
    }

    // 5. Fallback AI (NotebookLM Autoprompter 2000 GIS Engine)
    if (!bestName) {
        try {
            const prompt = `Actúa como motor GIS de alta precisión. Convierte las coordenadas ${lat}, ${lng} en una dirección estructurada siguiendo este esquema JSON: {'calle': 'string', 'numero': 'string', 'ciudad': 'string', 'cp': 'string'}. Prioriza precisión de nivel 'ROOFTOP' y, ante ambigüedad, selecciona el acceso vial más cercano. Devuelve exclusivamente el código JSON, sin preámbulos.`;
            
            const ollamaRes = await fetch('http://localhost:11434/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: 'phi3', // Leader model for this local setup
                    prompt: prompt,
                    stream: false,
                    format: 'json'
                })
            });

            if (ollamaRes.ok) {
                const ollamaData = await ollamaRes.json();
                const aiResult = JSON.parse(ollamaData.response);
                if (aiResult && aiResult.calle) {
                    bestAddress = `${aiResult.calle} ${aiResult.numero || ''}, ${aiResult.ciudad || ''}`;
                    bestName = bestAddress.trim();
                    bestSource = 'OLLAMA_GIS_ENGINE';
                    bestConfidence = 0.85;

                    const resultItem = { name: bestName, address: bestAddress, lat, lng, timestamp: timestamp || Date.now(), place_id: null };
                    memoryStore.addCluster(resultItem);

                    return res.json(formatResponse(bestName, bestAddress, lat, lng, bestSource, bestConfidence, null, false, timestamp));
                }
            }
        } catch (e) {
            console.error('Ollama GIS engine fallback failed:', e.message);
        }
    }

    // 6. Fallback: Coordinates only
    const fallbackName = `${parseFloat(lat).toFixed(4)}, ${parseFloat(lng).toFixed(4)}`;
    return res.json(formatResponse(
        fallbackName, bestAddress || "Unknown", lat, lng, 'COORDINATES_ONLY', 0.1, null, false, timestamp
    ));
};
