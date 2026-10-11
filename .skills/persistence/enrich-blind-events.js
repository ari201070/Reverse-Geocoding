// enrich-blind-events.js - 3-Step Workflow: Events → Sample → Heritage
// Ejecutar con: node enrich-blind-events.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { latLngToCell } from 'h3-js';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const EVENT_WINDOW_MS = 60 * 60 * 1000; // 60 minutes
const INHERIT_WINDOW_MS = 15 * 60 * 1000; // 15 minutes
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const OLLAMA_VISION_MODEL = process.env.OLLAMA_VISION_MODEL || 'moondream';

function roundCoord(val) {
    if (val === null || val === undefined) return null;
    return Math.round(val * 10000) / 10000;
}

async function callOllamaVision(imagePath) {
    try {
        const imageData = fs.readFileSync(imagePath);
        const base64 = imageData.toString('base64');
        
        const payload = {
            model: OLLAMA_VISION_MODEL,
            prompt: `Analyze this photo and act as an expert landmark and OCR detector.
You must return a JSON object with the following fields:
- "labels": Array of strings representing visual descriptors/tags.
- "landmarks": Array of strings representing names of specific landmarks or buildings.
- "texts": Array of strings representing any text, signs, logos visible in the photo (OCR).
Return ONLY the JSON object, with no markdown formatting, no backticks, and no explanation.`,
            images: [base64],
            stream: false,
            format: "json"
        };
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        const res = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        if (res.ok) {
            const data = await res.json();
            const text = data.response;
            if (text) {
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error('[Vision] JSON parse error:', e.message);
                    return null;
                }
            }
        }
    } catch (e) {
        console.error('[Vision] Error:', e.message);
    }
    return null;
}

function findPoiKeywords(labels, landmarks, texts) {
    const HIGH_RELEVANCE_KEYWORDS = [
        'catedral', 'plaza', 'museo', 'parque', 'monumento', 'jardin', 'mirador',
        'cerro', 'capilla', 'palacio', 'teatro', 'basilica', 'iglesia', 'cabildo',
        'facultad', 'universidad', 'estadio', 'obelisco', 'aeropuerto', 'estacion',
        'puente', 'monasterio', 'convento', 'santuario', 'cementerio', 'mercado',
        'cathedral', 'square', 'museum', 'park', 'monument', 'garden', 'lookout',
        'chapel', 'palace', 'theater', 'basilica', 'church', 'university', 'stadium',
        'obelisk', 'airport', 'station', 'bridge', 'monastery', 'market'
    ];
    
    const allText = [...(labels || []), ...(landmarks || []), ...(texts || [])].join(' ').toLowerCase();
    
    for (const kw of HIGH_RELEVANCE_KEYWORDS) {
        if (allText.includes(kw)) {
            return kw;
        }
    }
    return null;
}

async function runEnrichWorkflow() {
    console.log('=== ENRICH BLIND EVENTS - 3-STEP WORKFLOW ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // STEP 1: Group photos into 60-minute events
        console.log('[STEP 1] Agrupando fotos en eventos de 60 minutos...');
        
        const blindPhotos = await db.all(`
            SELECT id, file_path, filename, date_taken, latitude, longitude
            FROM photos 
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
            ORDER BY date_taken
        `);
        
        console.log(`    Encontradas ${blindPhotos.length} fotos sin GPS`);
        
        // Group into events by 60-min windows
        const events = [];
        let currentEvent = [];
        let lastTs = null;
        
        for (const photo of blindPhotos) {
            const ts = new Date(photo.date_taken).getTime();
            if (lastTs === null || (ts - lastTs) > EVENT_WINDOW_MS) {
                if (currentEvent.length > 0) {
                    events.push(currentEvent);
                }
                currentEvent = [photo];
            } else {
                currentEvent.push(photo);
            }
            lastTs = ts;
        }
        if (currentEvent.length > 0) {
            events.push(currentEvent);
        }
        
        console.log(`    Generados ${events.length} eventos de 60 minutos\n`);
        
        // STEP 2: Sample 1-2 photos per event and analyze
        console.log('[STEP 2] Muestreando y analizando fotos por evento...\n');
        
        let analyzed = 0;
        let enriched = 0;
        const sampleResults = [];
        
        for (let i = 0; i < events.length; i++) {
            const event = events[i];
            
            // Sample 1-2 photos from event
            const samples = event.slice(0, 2);
            
            for (const sample of samples) {
                if (!sample.file_path || !fs.existsSync(sample.file_path)) {
                    console.log(`  [${i+1}/${events.length}] Saltando ${sample.filename} - archivo no encontrado`);
                    continue;
                }
                
                console.log(`  [${i+1}/${events.length}] Analizando ${sample.filename}...`);
                
                const visionResult = await callOllamaVision(sample.file_path);
                
                if (visionResult) {
                    analyzed++;
                    
                    const poiKw = findPoiKeywords(visionResult.labels, visionResult.landmarks, visionResult.texts);
                    
                    if (visionResult.landmarks && visionResult.landmarks.length > 0) {
                        // Has landmark - potential anchor
                        sampleResults.push({
                            photo: sample,
                            vision: visionResult,
                            poiKeyword: poiKw,
                            eventIndex: i
                        });
                    }
                    
                    console.log(`      Labels: ${(visionResult.labels || []).slice(0, 3).join(', ')}`);
                    console.log(`      Landmarks: ${(visionResult.landmarks || []).join(', ')}`);
                    console.log(`      Texts: ${(visionResult.texts || []).slice(0, 2).join(' | ')}`);
                }
            }
            
            // Rate limit: wait 1 second between events
            if (i < events.length - 1) {
                await new Promise(r => setTimeout(r, 1000));
            }
        }
        
        console.log(`\n    Analizadas ${analyzed} fotos, ${sampleResults.length} con landmarks\n`);
        
        // STEP 3: Save new anchors and run Heritage
        console.log('[STEP 3] Guardando nuevas fotos ancla y ejecutando Heritage...\n');
        
        const updateStmt = await db.prepare(`
            UPDATE photos 
            SET latitude = ?, longitude = ?, 
                location_name = ?, city = ?, country = ?,
                date_source = 'VISION_LANDMARK'
            WHERE id = ?
        `);
        
        // For now, just report what we found
        console.log('=== RESULTADOS DEL ANÁLISIS ===');
        console.log(`Fotos analizadas: ${analyzed}`);
        console.log(`Con landmarks: ${sampleResults.length}`);
        
        if (sampleResults.length > 0) {
            console.log('\n--- Landmarks detectados ---');
            for (const r of sampleResults.slice(0, 10)) {
                console.log(`  ${r.photo.filename}: ${r.vision.landmarks.join(', ')}`);
                if (r.poiKeyword) {
                    console.log(`    POI keyword: ${r.poiKeyword}`);
                }
            }
        }
        
        console.log('\n✅ ENRICH WORKFLOW COMPLETADO');
        console.log('\nPróximos pasos:');
        console.log('1. Usar landmarks para buscar coordenadas via POI API');
        console.log('2. Guardar como fotos ancla');
        console.log('3. Ejecutar Heritage para propagar al resto del evento');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
        console.error(error.stack);
    } finally {
        await db.close();
    }
}

runEnrichWorkflow();
