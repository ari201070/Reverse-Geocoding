// api/find-poi.js — Geocoding Cascade Orchestrator (FOSS only)
// Levels: H3 Cache → Local DB → Photon → Overpass → OpenCage → Country boundary → Raw coords
import 'dotenv/config';
import memoryStore from './memory-store.js';
import * as h3 from 'h3-js';
import { contextualizeLandmarkName } from './utils/landmark-context.js';

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

export default async function handler(req, res) {
    if (req.method && req.method !== 'POST') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    const { latitude, longitude, lat, lng, radius = 50, keywords, camera_heading, direction } = req.body;
    
    const targetLat = parseFloat(latitude || lat);
    const targetLng = parseFloat(longitude || lng);
    const rawHeading = camera_heading !== undefined && camera_heading !== null ? camera_heading : direction;
    const targetHeading = rawHeading !== undefined && rawHeading !== null && rawHeading !== '' && !isNaN(parseFloat(rawHeading)) ? parseFloat(rawHeading) : null;

    console.log(`[QA DEBUG] Received Coord: ${targetLat}, ${targetLng}, Keywords: ${keywords}, Heading: ${targetHeading}`);

    if (isNaN(targetLat) || isNaN(targetLng)) {
        return res.status(400).json({ success: false, error: 'Invalid coordinates' });
    }

    const roundedLat = Math.round(targetLat * 10000) / 10000;
    const roundedLng = Math.round(targetLng * 10000) / 10000;
    const h3Index = h3.latLngToCell(roundedLat, roundedLng, 9);
    
    console.log(`[QA DEBUG] H3 Index (Res 9): ${h3Index}`);

    let result = null;

    // LEVEL 1: H3 Local Cache
    try {
        if (!process.env.DATABASE_URL) {
            console.warn('[QA WARN] DATABASE_URL no definida. Saltando Nivel 1 (Caché).');
        } else {
            const cachedPlace = await memoryStore.findMatch(h3Index, targetLat, targetLng, targetHeading);
            if (cachedPlace) {
                console.log(`[QA] Level 1 Hit (Cache): ${cachedPlace.name} (Confidence: ${cachedPlace.confidence})`);
                return res.json(formatResponse(
                    cachedPlace.name, null, targetLat, targetLng, 'LOCAL_CACHE_H3', cachedPlace.confidence || 1.0, cachedPlace.place_id, true
                ));
            }
        }
    } catch (e) {
        console.warn('[QA] Level 1 Cache Failure:', e.message);
    }

    // LEVEL 1.5: Local Radius DB
    try {
        const nearbyLocalPlace = await memoryStore.findNearby(targetLat, targetLng, radius);
        if (nearbyLocalPlace) {
            console.log(`[QA] Level 1.5 Hit (Local Radius DB): ${nearbyLocalPlace.name}`);
            return res.json(formatResponse(
                nearbyLocalPlace.name, null, targetLat, targetLng, 'LOCAL_SPATIAL_RADIUS_DB', nearbyLocalPlace.confidence || 0.95, nearbyLocalPlace.place_id, true
            ));
        }
    } catch (e) {
        console.warn('[QA] Level 1.5 Spatial Radius Failure:', e.message);
    }

    // LEVEL 2: FOSS External — Photon + Overpass
    console.log(`[QA FOSS] Local DB Cache Miss. Activating Photon & Overpass cascade...`);
    let photonResult = null;
    let overpassResult = null;

    try {
        const photonUrl = `https://photon.komoot.io/reverse?lon=${targetLng}&lat=${targetLat}`;
        console.log(`[QA FOSS] Querying Photon: ${photonUrl}`);
        const photonRes = await fetch(photonUrl, {
            headers: { 'User-Agent': 'ReverseGeocodingApp/1.0' }
        });
        if (photonRes.ok) {
            const data = await photonRes.json();
            if (data.features && data.features.length > 0) {
                const feat = data.features[0];
                const props = feat.properties;
                photonResult = {
                    name: props.name || props.street || `${targetLat.toFixed(4)}, ${targetLng.toFixed(4)}`,
                    street: props.street,
                    housenumber: props.housenumber,
                    city: props.city,
                    postcode: props.postcode,
                    country: props.country,
                    fullAddress: [
                        props.street ? (props.street + (props.housenumber ? ` ${props.housenumber}` : '')) : null,
                        props.city,
                        props.postcode,
                        props.country
                    ].filter(Boolean).join(', ')
                };
                console.log(`[QA FOSS] Photon match: ${photonResult.name} - ${photonResult.fullAddress}`);
            }
        }
    } catch (err) {
        console.warn('[QA FOSS] Photon reverse geocode failed:', err.message);
    }

    try {
        console.log(`[QA FOSS] Querying Overpass API in a ${radius}m radius`);
        const query = `[out:json][timeout:10];(node(around:${radius},${targetLat},${targetLng})[name];way(around:${radius},${targetLat},${targetLng})[name];relation(around:${radius},${targetLat},${targetLng})[name];);out tags center;`;
        const overpassUrl = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`;
        const overpassRes = await fetch(overpassUrl, {
            headers: { 'User-Agent': 'ReverseGeocodingApp/1.0' }
        });
        if (overpassRes.ok) {
            const data = await overpassRes.json();
            if (data.elements && data.elements.length > 0) {
                const candidates = data.elements.map(el => {
                    const center = el.center || { lat: el.lat, lon: el.lon };
                    return {
                        name: el.tags.name,
                        type: el.tags.tourism || el.tags.amenity || el.tags.historic || el.tags.building || el.tags.shop || el.tags.leisure || 'establishment',
                        lat: center.lat,
                        lng: center.lon,
                        tags: el.tags,
                        osm_id: el.id,
                        osm_type: el.type
                    };
                });

                const sorted = candidates.sort((a, b) => {
                    const getScore = (item) => {
                        let s = 0;
                        if (keywords) {
                            const kwList = keywords.toLowerCase().split(/\s+/).filter(k => k.length > 2);
                            kwList.forEach(kw => {
                                if (item.name?.toLowerCase().includes(kw)) s += 150;
                            });
                        }
                        const t = item.tags;
                        if (t.tourism === 'attraction' || t.tourism === 'museum') s += 100;
                        if (t.amenity === 'place_of_worship' || t.historic === 'monument' || t.historic === 'memorial') s += 90;
                        if (t.amenity === 'cafe' || t.amenity === 'restaurant' || t.amenity === 'pub') s += 80;
                        if (t.amenity === 'library' || t.amenity === 'theatre' || t.amenity === 'cinema') s += 70;
                        if (t.building && t.building !== 'yes') s += 40;
                        if (t.shop) s += 30;
                        const d = Math.sqrt(Math.pow(item.lat - targetLat, 2) + Math.pow(item.lng - targetLng, 2));
                        s -= d * 1000;
                        return s;
                    };
                    return getScore(b) - getScore(a);
                });

                const best = sorted[0];
                overpassResult = {
                    name: best.name,
                    type: best.type,
                    lat: best.lat,
                    lng: best.lng,
                    place_id: `osm_${best.osm_type}_${best.osm_id}`,
                    tags: best.tags
                };
                console.log(`[QA FOSS] Overpass best: ${overpassResult.name} (${overpassResult.type})`);
            }
        }
    } catch (err) {
        console.warn('[QA FOSS] Overpass API failed:', err.message);
    }

    if (overpassResult) {
        const finalName = contextualizeLandmarkName(overpassResult.name, photonResult?.fullAddress || "OpenStreetMap Area", overpassResult.lat, overpassResult.lng);
        await memoryStore.savePlace(overpassResult.place_id, finalName, overpassResult.type, overpassResult.lat, overpassResult.lng);
        return res.json(formatResponse(finalName, photonResult?.fullAddress || "OpenStreetMap Area", overpassResult.lat, overpassResult.lng, 'OSM_OVERPASS', 0.95, overpassResult.place_id, false));
    }

    if (photonResult) {
        const finalId = `photon_${Math.round(targetLat * 10000)}_${Math.round(targetLng * 10000)}`;
        await memoryStore.savePlace(finalId, photonResult.name, 'establishment', targetLat, targetLng);
        return res.json(formatResponse(photonResult.name, photonResult.fullAddress, targetLat, targetLng, 'OSM_PHOTON', 0.85, finalId, false));
    }

    // LEVEL 3: OpenCage Fallback
    const OPENCAGE_KEY = process.env.VITE_OPENCAGE_API_KEY;
    if (OPENCAGE_KEY) {
        try {
            const ocRes = await fetch(`https://api.opencagedata.com/geocode/v1/json?q=${roundedLat},${roundedLng}&key=${OPENCAGE_KEY}&language=es&no_annotations=1&no_record=true`);
            if (ocRes.ok) {
                const ocData = await ocRes.json();
                if (ocData.results && ocData.results.length > 0) {
                    const best = ocData.results[0];
                    const ocConfidence = (best.confidence || 0) / 10;
                    const name = best.components.tourism || best.components.landscape || best.components.pedestrian || best.formatted;

                    if (name.includes("Münster")) {
                        console.warn('[QA] OpenCage returned Münster. Ignoring as likely sandbox limitation.');
                    } else {
                        await memoryStore.savePlace('oc_' + (best.annotations?.MGRS || Date.now()), name, 'point_of_interest', targetLat, targetLng);
                        return res.json(formatResponse(name, best.formatted, targetLat, targetLng, 'OPENCAGE', ocConfidence, null, false));
                    }
                }
            }
        } catch (e) {
            console.warn('[QA] Level 3 OpenCage Failure:', e.message);
        }
    }

    // LEVEL 4: Local Country Boundary (H3 GeoJSON)
    try {
        const { findCountryForCoordinateWithH3 } = await import('./utils/spatial-utils.js');
        const countryInfo = findCountryForCoordinateWithH3(targetLat, targetLng);
        if (countryInfo && countryInfo.name && countryInfo.name !== "Ocean or Unknown") {
            console.log(`[QA] Level 4 Hit (Local GeoJSON H3): ${countryInfo.name}`);
            return res.json(formatResponse(
                `${countryInfo.name} (Local GeoJSON Map)`,
                `Continente: ${countryInfo.continent}, ISO: ${countryInfo.iso_a2_eh || countryInfo.iso_a2 || "XX"}`,
                targetLat, targetLng, 'LOCAL_COUNTRY_BOUNDARIES_H3', 0.85, countryInfo.h3Index, countryInfo.cached
            ));
        }
    } catch (e) {
        console.warn('[QA] Level 4 Local Country Fallback Failure:', e.message);
    }

    return res.json(formatResponse(
        `${roundedLat}, ${roundedLng}`, "Coordenadas puras (Sin resultados)", targetLat, targetLng, 'COORDINATES_ONLY', 0.1, null, false
    ));
}
