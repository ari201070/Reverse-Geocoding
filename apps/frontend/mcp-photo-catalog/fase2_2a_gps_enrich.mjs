/**
 * Fase 2.2a: Enriquecimiento GPS continuado (find-poi.js)
 * 
 * REGLAS:
 * - Solo fotos CON GPS y sin city
 * - Delay obligatorio de 1.1s entre llamadas
 * - Checkpoint cada 50 fotos
 * - NO usar Vision API
 */

import Database from 'better-sqlite3';
import fs from 'fs';

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const CHECKPOINT_PATH = './fase2_2a_checkpoint.json';
const OUTPUT_PATH = './resumen_fase2_2a.json';
const DELAY_MS = 1100;
const CHECKPOINT_EVERY = 50;

let lastApiCall = 0;
async function cooldown() {
  const now = Date.now();
  const elapsed = now - lastApiCall;
  if (elapsed < DELAY_MS) {
    await new Promise(r => setTimeout(r, DELAY_MS - elapsed));
  }
  lastApiCall = Date.now();
}

async function callPhoton(lat, lng) {
  try {
    const url = `https://photon.komoot.io/reverse?lon=${lng}&lat=${lat}`;
    const res = await fetch(url, { headers: { 'User-Agent': 'PhotoCatalogEnrichment/1.0' } });
    if (res.ok) {
      const data = await res.json();
      if (data.features && data.features.length > 0) {
        const props = data.features[0].properties;
        return {
          name: props.name || props.street || `${lat.toFixed(4)}, ${lng.toFixed(4)}`,
          city: props.city || null,
          state: props.state || null,
          country: props.country || null,
          source: 'PHOTON',
        };
      }
    }
  } catch (e) { /* ignore */ }
  return null;
}

async function callOverpass(lat, lng, radius = 500) {
  try {
    const query = `[out:json][timeout:10];(node(around:${radius},${lat},${lng})[name];way(around:${radius},${lat},${lng})[name];);out tags center;`;
    const url = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`;
    const res = await fetch(url, { headers: { 'User-Agent': 'PhotoCatalogEnrichment/1.0' } });
    if (res.ok) {
      const data = await res.json();
      if (data.elements && data.elements.length > 0) {
        const best = data.elements[0];
        const center = best.center || { lat: best.lat, lon: best.lon };
        return {
          name: best.tags.name,
          city: best.tags['addr:city'] || null,
          source: 'OVERPASS',
        };
      }
    }
  } catch (e) { /* ignore */ }
  return null;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 2.2a: ENRIQUECIMIENTO GPS CONTINUADO');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);
  
  // SQLite optimizations
  db.pragma('journal_mode = WAL');
  db.pragma('busy_timeout = 5000');
  console.log('✅ SQLite WAL mode + busy_timeout activados\n');

  // Load checkpoint
  let processedIds = new Set();
  if (fs.existsSync(CHECKPOINT_PATH)) {
    const checkpoint = JSON.parse(fs.readFileSync(CHECKPOINT_PATH, 'utf8'));
    processedIds = new Set(checkpoint.processedIds || []);
    console.log(`📋 Checkpoint cargado: ${processedIds.size} fotos ya procesadas`);
  }

  // Get candidates
  let query = `
    SELECT id, filename, country, city, latitude, longitude
    FROM photos 
    WHERE latitude IS NOT NULL 
      AND (city IS NULL OR city = '')
      AND (country != 'Israel' OR country IS NULL)
  `;
  if (processedIds.size > 0) {
    query += ` AND id NOT IN (${Array.from(processedIds).join(',')})`;
  }
  query += ` ORDER BY id`;

  const candidates = db.prepare(query).all();
  console.log(`\n📊 FOTOS CANDIDATAS: ${candidates.length.toLocaleString()}`);
  console.log(`⏱️  Tiempo estimado: ~${Math.ceil(candidates.length * DELAY_MS / 60000)} minutos\n`);

  const stats = { processed: 0, enriched: 0, failed: 0, by_source: {}, errors: [] };
  const updateStmt = db.prepare('UPDATE photos SET city = COALESCE(city, ?), location_name = COALESCE(location_name, ?) WHERE id = ?');

  for (let i = 0; i < candidates.length; i++) {
    const photo = candidates[i];
    try {
      await cooldown();
      let result = await callPhoton(photo.latitude, photo.longitude);
      if (!result || !result.city) {
        await cooldown();
        const overpass = await callOverpass(photo.latitude, photo.longitude);
        if (overpass) result = overpass;
      }
      if (result) {
        updateStmt.run(result.city || result.name, result.name, photo.id);
        stats.enriched++;
        stats.by_source[result.source] = (stats.by_source[result.source] || 0) + 1;
        if (stats.enriched % 10 === 0) {
          console.log(`  ✅ [${i + 1}/${candidates.length}] ${photo.filename} → ${result.city || result.name}`);
        }
      } else {
        stats.failed++;
      }
      stats.processed++;
      if (stats.processed % CHECKPOINT_EVERY === 0) {
        processedIds.add(photo.id);
        fs.writeFileSync(CHECKPOINT_PATH, JSON.stringify({
          processedIds: Array.from(processedIds),
          lastProcessed: photo.id,
          timestamp: new Date().toISOString(),
        }, null, 2));
        console.log(`  💾 Checkpoint: ${stats.processed}/${candidates.length}`);
      }
    } catch (e) {
      stats.failed++;
      stats.errors.push({ id: photo.id, error: e.message });
    }
  }

  // Final checkpoint
  fs.writeFileSync(CHECKPOINT_PATH, JSON.stringify({
    processedIds: Array.from(processedIds),
    completed: true,
    timestamp: new Date().toISOString(),
  }, null, 2));

  // Save summary
  stats.execution_time_minutes = Math.ceil(stats.processed * DELAY_MS / 60000);
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(stats, null, 2));

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  RESUMEN FASE 2.2a');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`📊 Procesadas: ${stats.processed.toLocaleString()}`);
  console.log(`✅ Enriquecidas: ${stats.enriched.toLocaleString()}`);
  console.log(`❌ Fallidas: ${stats.failed.toLocaleString()}`);
  console.log(`⏱️  Tiempo: ~${stats.execution_time_minutes} minutos`);

  db.close();
}

main().catch(console.error);
