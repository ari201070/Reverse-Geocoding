// enrich-argentina-events.js - Focus on Sep/Oct 2025 Argentina trip
// Ejecutar con: node enrich-argentina-events.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const EVENT_WINDOW_MS = 60 * 60 * 1000; // 60 minutes
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
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
        
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
                    return null;
                }
            }
        }
    } catch (e) {
        if (e.name !== 'AbortError') {
            console.error('[Vision] Error:', e.message);
        }
    }
    return null;
}

async function runEnrichWorkflow() {
    console.log('=== ENRICH ARGENTINA EVENTS - 3-STEP WORKFLOW ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // STEP 1: Get Argentina trip photos (Sep/Oct 2025) without GPS
        console.log('[STEP 1] Obteniendo fotos del viaje a Argentina (Sep/Oct 2025)...\n');
        
        const argentinaPhotos = await db.all(`
            SELECT id, file_path, filename, date_taken, latitude, longitude
            FROM photos 
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
              AND date_taken LIKE '2025-09-%'
            ORDER BY date_taken
        `);
        
        console.log(`    Encontradas ${argentinaPhotos.length} fotos de Argentina sin GPS\n`);
        
        // Group into events by 60-min windows
        const events = [];
        let currentEvent = [];
        let lastTs = null;
        
        for (const photo of argentinaPhotos) {
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
        let withLandmarks = 0;
        let withTexts = 0;
        const allResults = [];
        
        for (let i = 0; i < events.length; i++) {
            const event = events[i];
            const samples = event.slice(0, 2);
            
            for (const sample of samples) {
                if (!sample.file_path || !fs.existsSync(sample.file_path)) {
                    continue;
                }
                
                process.stdout.write(`  [${i+1}/${events.length}] ${sample.filename}... `);
                
                const visionResult = await callOllamaVision(sample.file_path);
                
                if (visionResult) {
                    analyzed++;
                    
                    const hasLandmarks = visionResult.landmarks && visionResult.landmarks.length > 0;
                    const hasTexts = visionResult.texts && visionResult.texts.length > 0;
                    
                    if (hasLandmarks) withLandmarks++;
                    if (hasTexts) withTexts++;
                    
                    allResults.push({
                        photo: sample,
                        vision: visionResult,
                        eventIndex: i
                    });
                    
                    if (hasLandmarks) {
                        console.log(`✓ Landmarks: ${visionResult.landmarks.join(', ')}`);
                    } else if (hasTexts) {
                        console.log(`✓ Texts: ${visionResult.texts.slice(0, 2).join(' | ')}`);
                    } else {
                        console.log(`✓ Labels: ${visionResult.labels.slice(0, 2).join(', ')}`);
                    }
                } else {
                    console.log(`✗ Timeout/Error`);
                }
            }
            
            // Rate limit
            if (i < events.length - 1) {
                await new Promise(r => setTimeout(r, 500));
            }
        }
        
        console.log(`\n    Análisis completado:`);
        console.log(`    - Fotos analizadas: ${analyzed}`);
        console.log(`    - Con landmarks: ${withLandmarks}`);
        console.log(`    - Con textos: ${withTexts}\n`);
        
        // STEP 3: Save results and report
        console.log('[STEP 3] Guardando resultados...\n');
        
        // Save results to JSON for further processing
        const outputPath = join(__dirname, 'argentina-vision-results.json');
        fs.writeFileSync(outputPath, JSON.stringify(allResults, null, 2));
        console.log(`    Resultados guardados en: ${outputPath}\n`);
        
        // Summary
        console.log('=== RESUMEN ===');
        console.log(`Total fotos Argentina sin GPS: ${argentinaPhotos.length}`);
        console.log(`Eventos de 60 min: ${events.length}`);
        console.log(`Fotos analizadas: ${analyzed}`);
        console.log(`Con landmarks detectados: ${withLandmarks}`);
        console.log(`Con textos detectados: ${withTexts}`);
        
        if (withLandmarks > 0) {
            console.log('\n--- Landmarks más comunes ---');
            const landmarkCounts = {};
            for (const r of allResults) {
                if (r.vision.landmarks) {
                    for (const lm of r.vision.landmarks) {
                        landmarkCounts[lm] = (landmarkCounts[lm] || 0) + 1;
                    }
                }
            }
            const sorted = Object.entries(landmarkCounts).sort((a, b) => b[1] - a[1]);
            for (const [lm, count] of sorted.slice(0, 10)) {
                console.log(`  ${lm}: ${count} fotos`);
            }
        }
        
        console.log('\n✅ ENRICH WORKFLOW COMPLETADO');
        console.log('\nPróximos pasos:');
        console.log('1. Revisar argentina-vision-results.json');
        console.log('2. Buscar coordenadas para landmarks detectados');
        console.log('3. Guardar como fotos ancla');
        console.log('4. Ejecutar Heritage para propagar');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
        console.error(error.stack);
    } finally {
        await db.close();
    }
}

runEnrichWorkflow();
