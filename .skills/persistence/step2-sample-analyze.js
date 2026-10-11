// step2-sample-analyze.js - Paso 2: Muestrear y analizar fotos por evento
// Ejecutar con: node step2-sample-analyze.js

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
const MAX_EVENTS = 100; // Process top 100 events first

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
        const timeoutId = setTimeout(() => controller.abort(), 60000);
        
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
        // Silently handle timeouts
    }
    return null;
}

async function sampleAndAnalyze() {
    console.log('=== STEP 2: MUESTREO Y ANÁLISIS POR EVENTO ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // Get all photos without GPS, ordered by date
        const blindPhotos = await db.all(`
            SELECT id, file_path, filename, date_taken
            FROM photos 
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
            ORDER BY date_taken
        `);
        
        // Group into events
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
        
        // Sort events by size (largest first) and take top MAX_EVENTS
        events.sort((a, b) => b.length - a.length);
        const eventsToProcess = events.slice(0, MAX_EVENTS);
        
        console.log(`Total eventos: ${events.length}`);
        console.log(`Procesando top ${eventsToProcess.length} eventos\n`);
        
        let analyzed = 0;
        let withLandmarks = 0;
        let withTexts = 0;
        const allResults = [];
        
        for (let i = 0; i < eventsToProcess.length; i++) {
            const event = eventsToProcess[i];
            
            // Sample 2 photos from event (middle and end)
            const samples = [];
            if (event.length >= 2) {
                samples.push(event[Math.floor(event.length / 2)]); // Middle
                samples.push(event[event.length - 1]); // End
            } else {
                samples.push(event[0]);
            }
            
            console.log(`[${i + 1}/${eventsToProcess.length}] Evento con ${event.length} fotos (${event[0].date_taken})`);
            
            for (const sample of samples) {
                if (!sample.file_path || !fs.existsSync(sample.file_path)) {
                    continue;
                }
                
                process.stdout.write(`  Analizando ${sample.filename}... `);
                
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
                        eventIndex: i,
                        eventSize: event.length
                    });
                    
                    if (hasLandmarks) {
                        console.log(`✓ Landmarks: ${visionResult.landmarks.join(', ')}`);
                    } else if (hasTexts) {
                        console.log(`✓ Texts: ${visionResult.texts.slice(0, 2).join(' | ')}`);
                    } else {
                        console.log(`✓ Labels: ${visionResult.labels.slice(0, 2).join(', ')}`);
                    }
                } else {
                    console.log(`✗ Timeout`);
                }
                
                // Small delay between samples
                await new Promise(r => setTimeout(r, 500));
            }
        }
        
        console.log(`\n=== RESUMEN ===`);
        console.log(`Eventos procesados: ${eventsToProcess.length}`);
        console.log(`Fotos analizadas: ${analyzed}`);
        console.log(`Con landmarks: ${withLandmarks}`);
        console.log(`Con textos: ${withTexts}\n`);
        
        // Save results
        const outputPath = join(__dirname, 'step2-vision-results.json');
        fs.writeFileSync(outputPath, JSON.stringify({
            totalEvents: events.length,
            processedEvents: eventsToProcess.length,
            analyzed: analyzed,
            withLandmarks: withLandmarks,
            withTexts: withTexts,
            results: allResults
        }, null, 2));
        
        console.log(`Resultados guardados en: ${outputPath}`);
        console.log('\n✅ STEP 2 COMPLETADO');
        console.log('\nPróximo paso: node step3-heritage-propagate.js');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
        console.error(error.stack);
    } finally {
        await db.close();
    }
}

sampleAndAnalyze();
