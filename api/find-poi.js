// api/find-poi.js - Real Google Places API (New) integration with Spatial Memory
// Uses Field Masking to control costs and avoid Enterprise SKUs

const memoryStore = require('./memory-store');

/**
 * POST /api/find-poi
 * Body: { lat, lng, timestamp, keywords, landmarkFromVision, radius }
 */
module.exports = async (req, res) => {
    if (req.method && req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { lat, lng, timestamp, keywords, landmarkFromVision, radius = 500 } = req.body;

    if (!lat || !lng) {
        return res.status(400).json({ error: 'lat and lng are required' });
    }

    const apiKey = process.env.GOOGLE_MAPS_API_KEY;

    // 1. Check Spatial Memory first (fast, free)
    const remembered = memoryStore.findMatch(lat, lng, timestamp);
    if (remembered) {
        return res.json({ status: 'SUCCESS', source: 'SPATIAL_MEMORY', data: remembered });
    }

    // 2. Try Google Places API (New) - Nearby Search
    if (apiKey) {
        try {
            const searchKeyword = landmarkFromVision || keywords || '';
            
            const placesUrl = 'https://places.googleapis.com/v1/places:searchNearby';
            const payload = {
                includedTypes: ['tourist_attraction', 'museum', 'park', 'landmark', 'establishment'],
                maxResultCount: 5,
                locationRestriction: {
                    circle: {
                        center: { latitude: lat, longitude: lng },
                        radius: radius
                    }
                }
            };

            // Add keyword hint if available (improves landmark precision)
            if (searchKeyword) {
                payload.rankPreference = 'RELEVANCE';
            }

            const placesRes = await fetch(placesUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // CRITICAL: Field Masking prevents Enterprise SKU charges
                    'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.types,places.location',
                    'X-Goog-Api-Key': apiKey
                },
                body: JSON.stringify(payload)
            });

            if (placesRes.ok) {
                const data = await placesRes.json();
                const places = data.places || [];

                if (places.length > 0) {
                    // Priority scoring: tourist_attraction > museum > park > other
                    const PRIORITY = { tourist_attraction: 100, museum: 90, park: 80, landmark: 70 };
                    
                    const best = places
                        .filter(p => {
                            const name = p.displayName?.text || '';
                            return !isGenericName(name);
                        })
                        .sort((a, b) => {
                            const scoreA = Math.max(...(a.types || []).map(t => PRIORITY[t] || 10));
                            const scoreB = Math.max(...(b.types || []).map(t => PRIORITY[t] || 10));
                            return scoreB - scoreA;
                        })[0] || places[0];

                    const result = {
                        name: best.displayName?.text || best.formattedAddress,
                        address: best.formattedAddress,
                        types: best.types,
                        landmark: landmarkFromVision || null,
                        lat,
                        lng,
                        timestamp: timestamp || Date.now()
                    };

                    // Save discovered location to spatial memory
                    memoryStore.addCluster(result);

                    return res.json({ status: 'SUCCESS', source: 'GOOGLE_PLACES_NEW', data: result });
                }
            }

            // 3. Fallback: Geocoding API (address-level, cheaper)
            const geocodeUrl = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${apiKey}&result_type=point_of_interest|establishment|premise`;
            const geocodeRes = await fetch(geocodeUrl);
            
            if (geocodeRes.ok) {
                const gData = await geocodeRes.json();
                if (gData.results && gData.results.length > 0) {
                    const best = gData.results[0];
                    const name = best.formatted_address.split(',')[0];
                    const result = {
                        name,
                        address: best.formatted_address,
                        types: best.types,
                        landmark: landmarkFromVision || null,
                        lat,
                        lng,
                        timestamp: timestamp || Date.now()
                    };
                    memoryStore.addCluster(result);
                    return res.json({ status: 'SUCCESS', source: 'GEOCODING_API', data: result });
                }
            }
        } catch (err) {
            console.error('Google Places API error:', err.message);
        }
    }

    // 4. No API key or all APIs failed: return coordinates only
    const fallbackResult = {
        name: landmarkFromVision || `${parseFloat(lat).toFixed(4)}, ${parseFloat(lng).toFixed(4)}`,
        address: null,
        landmark: landmarkFromVision || null,
        lat,
        lng,
        timestamp: timestamp || Date.now()
    };
    return res.json({ status: 'PARTIAL', source: 'COORDINATES_ONLY', data: fallbackResult });
};

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
