// Vercel Serverless Function (Node 18+). Rutas: /api/find-poi
// Recibe POST { latitude, longitude, radius, keywords }
// Usa GOOGLE_MAPS_API_KEY definido en Variables de Entorno (Vercel Project Settings)
// Implementa: Text Search (si keywords), Nearby Search (rankby=distance), Place Details, fallback reverse geocode
// Añade retry/backoff para 429 y cache simple en memoria (TTL).

const CACHE_TTL_MS = 1000 * 60 * 60 * 24 * 7; // 7 días
const POI_DISTANCE_THRESHOLD_M = 500; // Default (frontend puede ajustar radius en payload)

const cache = new Map(); // key -> { ts, value }

function cacheKey(lat, lng) {
  // agrupar con 4 decimales
  const key = `${lat.toFixed(4)},${lng.toFixed(4)}`;
  return key;
}

function nowMs() { return Date.now(); }

async function sleep(ms) { return new Promise(res => setTimeout(res, ms)); }

async function retryFetch(url, opts = {}, attempts = 3, delay = 700) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      const r = await fetch(url, opts);
      if (r.status === 429) {
        lastErr = { status: 429, message: '429' };
        await sleep(delay * Math.pow(2, i));
        continue;
      }
      return r;
    } catch (e) {
      lastErr = e;
      await sleep(delay * Math.pow(2, i));
    }
  }
  throw lastErr;
}

async function getJson(url, opts = {}) {
  const res = await retryFetch(url, opts);
  const text = await res.text();
  try {
    return { ok: res.ok, status: res.status, json: JSON.parse(text) };
  } catch (e) {
    return { ok: res.ok, status: res.status, json: text };
  }
}

function distanceMeters(lat1, lon1, lat2, lon2) {
  function toRad(v) { return v * Math.PI / 180; }
  const R = 6371000;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body;
  const lat = Number(body.latitude);
  const lng = Number(body.longitude);
  const radius = Number(body.radius || 500);
  const keywords = body.keywords || null;

  if (!lat || !lng) {
    res.status(400).json({ error: 'latitude and longitude required' });
    return;
  }

  const apiKey = process.env.GOOGLE_MAPS_API_KEY;
  if (!apiKey) {
    res.status(500).json({ error: 'GOOGLE_MAPS_API_KEY not configured in server' });
    return;
  }

  // Cache check
  const ckey = cacheKey(lat, lng);
  const entry = cache.get(ckey);
  if (entry && (nowMs() - entry.ts) < CACHE_TTL_MS) {
    res.status(200).json({ source: 'cache', place: entry.value.place, distanceMeters: entry.value.distanceMeters });
    return;
  }

  try {
    // 1) If keywords provided try Text Search nearby (radius)
    if (keywords && keywords.trim().length > 0) {
      const q = encodeURIComponent(keywords.trim());
      // For specific and important keywords, we expand search slightly
      const searchRadius = Math.max(radius, 1000); 
      const textUrl = `https://maps.googleapis.com/maps/api/place/textsearch/json?query=${q}&location=${lat},${lng}&radius=${searchRadius}&key=${apiKey}&language=es`;
      const textResp = await getJson(textUrl);

      if (textResp.ok && Array.isArray(textResp.json.results) && textResp.json.results.length > 0) {
        // Sort by distance to favor local matches, but return anything within 1.5km
        const filteredResults = textResp.json.results
          .map(r => ({ ...r, dist: distanceMeters(lat, lng, r.geometry.location.lat, r.geometry.location.lng) }))
          .filter(r => r.dist <= 1500)
          .sort((a,b) => a.dist - b.dist);

        if (filteredResults.length > 0) {
          const r = filteredResults[0];
          const d = r.dist;
          
          if (r.place_id) {
            const detUrl = `https://maps.googleapis.com/maps/api/place/details/json?place_id=${r.place_id}&fields=name,formatted_address,geometry,types,plus_code&key=${apiKey}&language=es`;
            const detResp = await getJson(detUrl);
            if (detResp.ok && detResp.json.result) {
              const place = detResp.json.result;
              cache.set(ckey, { ts: nowMs(), value: { place, distanceMeters: Math.round(d) } });
              res.status(200).json({ source: 'text_search_place_details', distanceMeters: Math.round(d), place });
              return;
            }
          }
          // fallback basic
          const placeBasic = { name: r.name, formatted_address: r.formatted_address, geometry: r.geometry, types: r.types, plus_code: r.plus_code };
          cache.set(ckey, { ts: nowMs(), value: { place: placeBasic, distanceMeters: Math.round(d) } });
          res.status(200).json({ source: 'text_search_basic', distanceMeters: Math.round(d), place: placeBasic });
          return;
        }
      }
    }

    // 2) Nearby searches by types using rankby=distance (no radius)
    let typesToTry = ['park','tourist_attraction','museum','art_gallery','zoo','aquarium'];
    
    const kLower = keywords ? keywords.toLowerCase() : "";
    const isNature = kLower.includes('leisure') || kLower.includes('tree') || kLower.includes('natural') || kLower.includes('nature') || kLower.includes('outdoor') || kLower.includes('plant') || kLower.includes('grass') || kLower.includes('landscape') || kLower.includes('white') || kLower.includes('flat') || kLower.includes('snow') || kLower.includes('winter');
    const isCulture = kLower.includes('sculpture') || kLower.includes('statue') || kLower.includes('art') || kLower.includes('monument') || kLower.includes('landmark');
    const isFood = kLower.includes('food') || kLower.includes('dish') || kLower.includes('cuisine') || kLower.includes('meal') || kLower.includes('tableware') || kLower.includes('ingredient') || kLower.includes('restaurant') || kLower.includes('cafe');
    
    // Prioritizing based on detected context
    if (isFood) {
      typesToTry = ['restaurant', 'cafe', 'bakery', 'bar', 'food', ...typesToTry];
    } else if (isCulture) {
      typesToTry = ['tourist_attraction', 'museum', 'art_gallery', 'park', 'place_of_worship'];
    } else if (isNature) {
      // For nature, we also want natural_feature which covers things like "Salinas Grandes"
      typesToTry = ['natural_feature', 'park', 'zoo', 'aquarium', 'tourist_attraction', 'point_of_interest'];
    }
    
    const fallbackTypes = ['point_of_interest', 'establishment', 'lodging'];
    const allTypesToSearch = [...new Set([...typesToTry, ...fallbackTypes])];

    let candidates = [];

    // Collect candidates from multiple types
    for (const type of allTypesToSearch) {
      const nearUrl = `https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=${lat},${lng}&rankby=distance&type=${encodeURIComponent(type)}&key=${apiKey}&language=es`;
      const nearResp = await getJson(nearUrl);
      if (nearResp.ok && Array.isArray(nearResp.json.results)) {
        for (const r of nearResp.json.results) {
          // Deduplicate
          if (candidates.some(c => c.place_id === r.place_id)) continue;
          
          const d = distanceMeters(lat, lng, r.geometry.location.lat, r.geometry.location.lng);
          
          // Basic distance check (generous for keywords, tight for generic)
          const isVast = (r.types || []).some(t => ['park', 'natural_feature', 'tourist_attraction'].includes(t));
          const maxDist = isVast ? Math.max(radius, 1200) : radius;
          
          if (d <= maxDist) {
            candidates.push({ ...r, dist: d });
          }
        }
      }
      if (candidates.length > 15) break; 
    }

    if (candidates.length > 0) {
      // RANKING LOGIC
      const ranked = candidates.sort((a,b) => {
        const score = (res) => {
          let s = 1000 - (res.dist / 2); // Base score by proximity
          
          const name = res.name.toLowerCase();
          const types = res.types || [];
          
          // 1. Keyword bonus (The most powerful signal)
          if (keywords) {
            const keys = keywords.toLowerCase().split(' ').filter(k => k.length > 3);
            keys.forEach(k => {
              if (name.includes(k)) s += 1000; // Found detected text in name!
            });
          }
          
          // 2. Type relevance
          if (types.includes('tourist_attraction')) s += 200;
          if (types.includes('amusement_park')) s += 500; // Big boost for theme parks
          if (types.includes('park')) s += 50;
          
          // 3. Penalty for generic names (using regex or substring)
          const genericTerms = ['costanera', 'avenida', 'calle', 'ruta', 'plaza'];
          genericTerms.forEach(t => { if (name.includes(t)) s -= 300; });

          return s;
        };
        return score(b) - score(a);
      });

      const best = ranked[0];
      
      // Get details for the winner
      if (best.place_id) {
        const detUrl = `https://maps.googleapis.com/maps/api/place/details/json?place_id=${best.place_id}&fields=name,formatted_address,geometry,types,plus_code&key=${apiKey}&language=es`;
        const detResp = await getJson(detUrl);
        if (detResp.ok && detResp.json.result) {
          const resData = detResp.json.result;
          const finalCandidate = { 
            source: 'ranked_nearby_details', 
            distanceMeters: Math.round(best.dist), 
            place: resData,
            plus_code: resData.plus_code || best.plus_code
          };
          cache.set(ckey, { ts: nowMs(), value: finalCandidate });
          res.status(200).json(finalCandidate);
          return;
        }
      }

      const basicCandidate = { 
        source: 'ranked_nearby_basic', 
        distanceMeters: Math.round(best.dist), 
        place: best,
        plus_code: best.plus_code 
      };
      cache.set(ckey, { ts: nowMs(), value: basicCandidate });
      res.status(200).json(basicCandidate);
      return;
    }

    // 3) Fallback Reverse Geocode
    const geocodeUrl = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${apiKey}&language=es`;
    const geoResp = await getJson(geocodeUrl);
    if (geoResp.ok && Array.isArray(geoResp.json.results) && geoResp.json.results.length > 0) {
      const poi = geoResp.json.results.find(r => (r.types || []).some(t => ['point_of_interest','establishment','park','tourist_attraction', 'natural_feature'].includes(t)));
      const best = poi || geoResp.json.results[0];
      const place = { 
        name: best.formatted_address, 
        formatted_address: best.formatted_address, 
        types: best.types, 
        geometry: best.geometry,
        plus_code: best.plus_code 
      };
      const finalRes = { source: 'reverse_geocode', place, plus_code: best.plus_code };
      cache.set(ckey, { ts: nowMs(), value: finalRes });
      res.status(200).json(finalRes);
      return;
    }

    res.status(200).json({ source: 'none', place: null });

  } catch (err) {
    console.error('find-poi error', err);
    res.status(500).json({ error: String(err) });
  }
}
