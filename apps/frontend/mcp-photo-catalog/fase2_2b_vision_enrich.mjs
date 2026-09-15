/**
 * Fase 2.2b: Fallback Ollama/Moondream para fotos sin GPS
 * 
 * REGLAS:
 * - Solo fotos SIN GPS y sin trip_name
 * - Usar Ollama local con moondream
 * - Delay de 2s entre llamadas
 * - Checkpoint cada 20 fotos
 * - SQLite WAL mode + busy_timeout
 * - Redimensionar imágenes a 1024px con sharp
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import sharp from 'sharp';

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const CHECKPOINT_PATH = './fase2_2b_checkpoint.json';
const OUTPUT_PATH = './resumen_fase2_2b.json';
const DELAY_MS = 2000;
const CHECKPOINT_EVERY = 20;
const OLLAMA_URL = 'http://127.0.0.1:11434';
const MAX_IMAGE_WIDTH = 1024;

let lastApiCall = 0;
async function cooldown() {
  const now = Date.now();
  const elapsed = now - lastApiCall;
  if (elapsed < DELAY_MS) {
    await new Promise(r => setTimeout(r, DELAY_MS - elapsed));
  }
  lastApiCall = Date.now();
}

async function resizeImage(imagePath) {
  try {
    const imageBuffer = fs.readFileSync(imagePath);
    const resized = await sharp(imageBuffer)
      .resize({ width: MAX_IMAGE_WIDTH, withoutEnlargement: true })
      .jpeg({ quality: 80 })
      .toBuffer();
    return resized.toString('base64');
  } catch (e) {
    // Fallback to original if sharp fails
    const imageBuffer = fs.readFileSync(imagePath);
    return imageBuffer.toString('base64');
  }
}

async function analyzeWithOllama(imagePath) {
  try {
    const imageBase64 = await resizeImage(imagePath);
    
    const payload = {
      model: 'moondream',
      prompt: `Analyze this photo and return a JSON object with:
- "country": Country name (if identifiable)
- "city": City/town name (if identifiable)
- "landmark": Specific landmark or POI name (if identifiable)
- "description": Brief description of the scene
Return ONLY the JSON, no markdown formatting.`,
      images: [imageBase64],
      stream: false,
      format: "json"
    };

    const res = await fetch(`${OLLAMA_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(60000), // 60s timeout
    });

    if (res.ok) {
      const data = await res.json();
      try {
        return JSON.parse(data.response);
      } catch {
        return null;
      }
    }
  } catch (e) {
    console.warn(`  ⚠️ Ollama failed: ${e.message}`);
  }
  return null;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 2.2b: FALLBACK VISION - OLLAMA MOONDREAM');
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
    console.log(`📋 Checkpoint cargado: ${processedIds.size} fotos procesadas`);
  }

  // Get candidates (no GPS, no trip, not Israel)
  let query = `
    SELECT id, file_path, filename, country, trip_name
    FROM photos 
    WHERE latitude IS NULL 
      AND (trip_name IS NULL OR trip_name = '')
      AND (country != 'Israel' OR country IS NULL)
      AND file_ext IN ('.jpg', '.jpeg', '.png', '.webp')
  `;
  if (processedIds.size > 0) {
    query += ` AND id NOT IN (${Array.from(processedIds).join(',')})`;
  }
  query += ` ORDER BY id LIMIT 500`;

  const candidates = db.prepare(query).all();
  console.log(`\n📊 FOTOS CANDIDATAS: ${candidates.length.toLocaleString()}`);
  console.log(`⏱️  Tiempo estimado: ~${Math.ceil(candidates.length * DELAY_MS / 60000)} minutos\n`);

  const stats = { processed: 0, enriched: 0, failed: 0, by_country: {}, errors: [] };
  const updateStmt = db.prepare('UPDATE photos SET country = COALESCE(country, ?), city = COALESCE(city, ?), location_name = COALESCE(location_name, ?) WHERE id = ?');

  for (let i = 0; i < candidates.length; i++) {
    const photo = candidates[i];
    try {
      // Check if file exists
      if (!fs.existsSync(photo.file_path)) {
        stats.failed++;
        stats.processed++;
        continue;
      }

      await cooldown();
      const result = await analyzeWithOllama(photo.file_path);
      
      if (result && (result.country || result.city || result.landmark)) {
        updateStmt.run(
          result.country || null,
          result.city || result.landmark || null,
          result.landmark || result.description || null,
          photo.id
        );
        stats.enriched++;
        stats.by_country[result.country || 'Unknown'] = (stats.by_country[result.country || 'Unknown'] || 0) + 1;
        if (stats.enriched % 5 === 0) {
          console.log(`  ✅ [${i + 1}/${candidates.length}] ${photo.filename} → ${result.country || 'N/A'} / ${result.city || result.landmark || 'N/A'}`);
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
  stats.by_country = Object.entries(stats.by_country).map(([country, cnt]) => ({ country, cnt })).sort((a, b) => b.cnt - a.cnt);
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(stats, null, 2));

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  RESUMEN FASE 2.2b');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`📊 Procesadas: ${stats.processed.toLocaleString()}`);
  console.log(`✅ Enriquecidas: ${stats.enriched.toLocaleString()}`);
  console.log(`❌ Fallidas: ${stats.failed.toLocaleString()}`);
  console.log(`⏱️  Tiempo: ~${stats.execution_time_minutes} minutos`);

  db.close();
}

main().catch(console.error);
