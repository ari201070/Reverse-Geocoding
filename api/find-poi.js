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
      const textUrl = `https://maps.googleapis.com/maps/api/place/textsearch/json?query=${q}&location=${lat},${lng}&radius=${radius}&key=${apiKey}&language=es`;
      const textResp = await getJson(textUrl);
      if (textResp.ok && Array.isArray(textResp.json.results) && textResp.json.results.length > 0) {
        for (const r of textResp.json.results) {
          const loc = r.geometry && r.geometry.location;
          if (!loc) continue;
          const d = distanceMeters(lat, lng, loc.lat, loc.lng);
          if (d <= POI_DISTANCE_THRESHOLD_M) {
            // Get details if possible
            if (r.place_id) {
              const detUrl = `https://maps.googleapis.com/maps/api/place/details/json?place_id=${r.place_id}&fields=name,formatted_address,geometry,types&key=${apiKey}&language=es`;
              const detResp = await getJson(detUrl);
              if (detResp.ok && detResp.json.result) {
                const place = detResp.json.result;
                cache.set(ckey, { ts: nowMs(), value: { place, distanceMeters: Math.round(d) } });
                res.status(200).json({ source: 'text_search_place_details', distanceMeters: Math.round(d), place });
                return;
              }
            }
            // fallback basic
            const placeBasic = { name: r.name, formatted_address: r.formatted_address, geometry: r.geometry, types: r.types };
            cache.set(ckey, { ts: nowMs(), value: { place: placeBasic, distanceMeters: Math.round(d) } });
            res.status(200).json({ source: 'text_search_basic', distanceMeters: Math.round(d), place: placeBasic });
            return;
          }
        }
      }
    }

    // 2) Nearby searches by types using rankby=distance (no radius)
    const typesToTry = ['park','point_of_interest','tourist_attraction','establishment','restaurant','museum','lodging'];
    for (const type of typesToTry) {
      const nearUrl = `https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=${lat},${lng}&rankby=distance&type=${encodeURIComponent(type)}&key=${apiKey}&language=es`;
      const nearResp = await getJson(nearUrl);
      if (nearResp.ok && Array.isArray(nearResp.json.results) && nearResp.json.results.length > 0) {
        for (const r of nearResp.json.results) {
          const loc = r.geometry && r.geometry.location;
          if (!loc) continue;
          const d = distanceMeters(lat, lng, loc.lat, loc.lng);
          if (d <= Math.max(radius, POI_DISTANCE_THRESHOLD_M)) {
            // place details
            if (r.place_id) {
              const detUrl = `https://maps.googleapis.com/maps/api/place/details/json?place_id=${r.place_id}&fields=name,formatted_address,geometry,types&key=${apiKey}&language=es`;
              const detResp = await getJson(detUrl);
              if (detResp.ok && detResp.json.result) {
                const place = detResp.json.result;
                cache.set(ckey, { ts: nowMs(), value: { place, distanceMeters: Math.round(d) } });
                res.status(200).json({ source: 'nearby_place_details', typeSearched: type, distanceMeters: Math.round(d), place });
                return;
              }
            }
            // fallback nearby basic
            const placeBasic = { name: r.name, vicinity: r.vicinity, geometry: r.geometry, types: r.types };
            cache.set(ckey, { ts: nowMs(), value: { place: placeBasic, distanceMeters: Math.round(d) } });
            res.status(200).json({ source: 'nearby_basic', typeSearched: type, distanceMeters: Math.round(d), place: placeBasic });
            return;
          }
        }
      }
    }

    // 3) Fallback Reverse Geocode
    const geocodeUrl = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${apiKey}&language=es`;
    const geoResp = await getJson(geocodeUrl);
    if (geoResp.ok && Array.isArray(geoResp.json.results) && geoResp.json.results.length > 0) {
      const poi = geoResp.json.results.find(r => (r.types || []).some(t => ['point_of_interest','establishment','park','tourist_attraction'].includes(t)));
      const best = poi || geoResp.json.results[0];
      const place = { formatted_address: best.formatted_address, types: best.types, address_components: best.address_components, geometry: best.geometry };
      cache.set(ckey, { ts: nowMs(), value: { place, distanceMeters: null } });
      res.status(200).json({ source: 'reverse_geocode', place });
      return;
    }

    res.status(200).json({ source: 'none', place: null });

  } catch (err) {
    console.error('find-poi error', err);
    res.status(500).json({ error: String(err) });
  }
}
