/**
 * Fase 2.2: Enriquecimiento GPS con find-poi.js
 * 
 * REGLAS:
 * - Delay obligatorio de 1.1s entre llamadas
 * - Checkpoint cada 50 fotos
 * - Solo fotos internacionales (no Israel)
 * - Guardado progresivo en DB
 * - Generar resumen_fase2_2.json
 */

import Database from 'better-sqlite3';
import fs from 'fs';

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const OUTPUT_PATH = './resumen_fase2_2.json';
const CHECKPOINT_PATH = './fase2_2_checkpoint.json';
const DELAY_MS = 1100; // 1.1 seconds
const CHECKPOINT_EVERY = 50;

// Cooldown anti-saturation
let lastApiCall = 0;
async function cooldown() {
  const now = Date.now();
  const elapsed = now - lastApiCall;
  if (elapsed < DELAY_MS) {
    await new Promise(r => setTimeout(r, DELAY_MS - elapsed));
  }
  lastApiCall = Date.now();
}

// Call Photon API for reverse geocoding
async function callPhoton(lat, lng) {
  try {
    const url = `https://photon.komoot.io/reverse?lon=${lng}&lat=${lat}`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'PhotoCatalogEnrichment/1.0' }
    });
    
    if (res.ok) {
      const data = await res.json();
      if (data.features && data.features.length > 0) {
        const feat = data.features[0];
        const props = feat.properties;
        return {
          name: props.name || props.street || `${lat.toFixed(4)}, ${lng.toFixed(4)}`,
          city: props.city || null,
          state: props.state || null,
          country: props.country || null,
          postcode: props.postcode || null,
          source: 'PHOTON',
          confidence: 0.85,
        };
      }
    }
  } catch (e) {
    console.warn('  ⚠️ Photon failed:', e.message);
  }
  return null;
}

// Call Overpass API for nearby POIs
async function callOverpass(lat, lng, radius = 500) {
  try {
    const query = `[out:json][timeout:10];(node(around:${radius},${lat},${lng})[name];way(around:${radius},${lat},${lng})[name];relation(around:${radius},${lat},${lng})[name];);out tags center;`;
    const url = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'PhotoCatalogEnrichment/1.0' }
    });
    
    if (res.ok) {
      const data = await res.json();
      if (data.elements && data.elements.length > 0) {
        const best = data.elements[0];
        const center = best.center || { lat: best.lat, lon: best.lon };
        return {
          name: best.tags.name,
          type: best.tags.tourism || best.tags.amenity || best.tags.historic || 'point_of_interest',
          lat: center.lat,
          lng: center.lon,
          city: best.tags['addr:city'] || null,
          source: 'OVERPASS',
          confidence: 0.95,
        };
      }
    }
  } catch (e) {
    console.warn('  ⚠️ Overpass failed:', e.message);
  }
  return null;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 2.2: ENRIQUECIMIENTO GPS CON FIND-POI');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);

  // 1. Load checkpoint if exists
  let processedIds = new Set();
  if (fs.existsSync(CHECKPOINT_PATH)) {
    const checkpoint = JSON.parse(fs.readFileSync(CHECKPOINT_PATH, 'utf8'));
    processedIds = new Set(checkpoint.processedIds || []);
    console.log(`📋 Checkpoint cargado: ${processedIds.size} fotos ya procesadas`);
  }

  // 2. Get candidate photos
  let query = `
    SELECT id, file_path, filename, country, city, location_name, latitude, longitude
    FROM photos 
    WHERE latitude IS NOT NULL 
      AND (city IS NULL OR city = '' OR location_name IS NULL OR location_name = '')
      AND (country != 'Israel' OR country IS NULL)
  `;
  
  if (processedIds.size > 0) {
    query += ` AND id NOT IN (${Array.from(processedIds).join(',')})`;
  }
  
  query += ` ORDER BY id`;
  
  const candidates = db.prepare(query).all();

  console.log(`\n📊 FOTOS CANDIDATAS: ${candidates.length.toLocaleString()}`);
  console.log(`⏱️  Tiempo estimado: ~${Math.ceil(candidates.length * DELAY_MS / 60000)} minutos\n`);

  // 3. Process candidates
  const stats = {
    total: candidates.length,
    processed: 0,
    enriched: 0,
    failed: 0,
    by_source: { PHOTON: 0, OVERPASS: 0 },
    by_country: {},
    errors: [],
  };

  const updateStmt = db.prepare(`
    UPDATE photos SET 
      city = COALESCE(city, ?),
      location_name = COALESCE(location_name, ?),
      location_address = COALESCE(location_address, ?)
    WHERE id = ?
  `);

  for (let i = 0; i < candidates.length; i++) {
    const photo = candidates[i];
    
    try {
      // Cooldown
      await cooldown();
      
      // Try Photon first
      let result = await callPhoton(photo.latitude, photo.longitude);
      
      // If no city from Photon, try Overpass
      if (!result || !result.city) {
        await cooldown();
        const overpassResult = await callOverpass(photo.latitude, photo.longitude);
        if (overpassResult) {
          result = overpassResult;
        }
      }
      
      if (result) {
        // Update DB
        const city = result.city || result.name;
        const locationName = result.name;
        const address = [result.city, result.state, result.country].filter(Boolean).join(', ');
        
        updateStmt.run(city, locationName, address, photo.id);
        
        stats.enriched++;
        stats.by_source[result.source] = (stats.by_source[result.source] || 0) + 1;
        stats.by_country[photo.country] = (stats.by_country[photo.country] || 0) + 1;
        
        if (stats.enriched % 10 === 0) {
          console.log(`  ✅ [${i + 1}/${candidates.length}] Enriched: ${photo.filename} → ${city}`);
        }
      } else {
        stats.failed++;
        stats.errors.push({ id: photo.id, filename: photo.filename, error: 'No results from APIs' });
      }
      
      stats.processed++;
      
      // Checkpoint
      if (stats.processed % CHECKPOINT_EVERY === 0) {
        processedIds.add(photo.id);
        try {
          fs.writeFileSync(CHECKPOINT_PATH, JSON.stringify({
            processedIds: Array.from(processedIds),
            lastProcessed: photo.id,
            timestamp: new Date().toISOString(),
          }, null, 2));
          console.log(`  💾 Checkpoint: ${stats.processed}/${candidates.length} procesadas`);
        } catch (e) {
          console.warn('  ⚠️ Failed to save checkpoint:', e.message);
        }
      }
      
    } catch (e) {
      stats.failed++;
      stats.errors.push({ id: photo.id, filename: photo.filename, error: e.message });
      console.error(`  ❌ Error processing ${photo.id}: ${e.message}`);
    }
  }

  // 4. Final checkpoint
  fs.writeFileSync(CHECKPOINT_PATH, JSON.stringify({
    processedIds: Array.from(processedIds),
    lastProcessed: candidates[candidates.length - 1]?.id,
    timestamp: new Date().toISOString(),
    completed: true,
  }, null, 2));

  // 5. Save summary
  stats.by_country = Object.entries(stats.by_country)
    .map(([country, cnt]) => ({ country, cnt }))
    .sort((a, b) => b.cnt - a.cnt);
  
  stats.execution_time_ms = candidates.length * DELAY_MS;
  stats.execution_time_minutes = Math.ceil(stats.execution_time_ms / 60000);

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(stats, null, 2));
  console.log(`\n✅ Resumen guardado en: ${OUTPUT_PATH}`);

  // 6. Print summary
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  RESUMEN EJECUTIVO');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`📊 Total procesadas: ${stats.processed.toLocaleString()}`);
  console.log(`✅ Enriquecidas: ${stats.enriched.toLocaleString()}`);
  console.log(`❌ Fallidas: ${stats.failed.toLocaleString()}`);
  console.log(`⏱️  Tiempo: ~${stats.execution_time_minutes} minutos`);
  console.log('\n🔹 Por fuente:');
  Object.entries(stats.by_source).forEach(([source, cnt]) => {
    console.log(`  ${source}: ${cnt.toLocaleString()}`);
  });
  console.log('\n🔹 Por país:');
  stats.by_country.forEach(c => {
    console.log(`  ${c.country}: ${c.cnt.toLocaleString()}`);
  });

  db.close();
}

main().catch(console.error);
