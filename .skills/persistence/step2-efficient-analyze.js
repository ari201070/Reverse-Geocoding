// step2-efficient-analyze.js - Efficient analysis using server API
// Ejecutar con: node step2-efficient-analyze.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const EVENT_WINDOW_MS = 60 * 60 * 1000; // 60 minutes
const SERVER_URL = process.env.SERVER_URL || 'http://localhost:3000';
const MAX_EVENTS = 50; // Process top 50 events

async function callAnalyzeImage(imagePath, lat, lng, timestamp) {
    try {
        const imageData = fs.readFileSync(imagePath);
        const base64 = imageData.toString('base64');
        
        const res = await fetch(`${SERVER_URL}/api/analyze-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_base64: base64,
                lat: lat,
                lng: lng,
                timestamp: timestamp,
                current_step: 'HERITAGE',
                mime_type: 'image/jpeg'
            })
        });
        
        if (res.ok) {
            return await res.json();
        }
    } catch (e) {
        // Silently handle errors
    }
    return null;
}

async function efficientAnalyze() {
    console.log('=== STEP 2: EFFICIENT ANALYSIS VIA SERVER API ===\n');
    
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
        
        // Sort events by size and take top MAX_EVENTS
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
            
            // Sample 1 photo from middle of event
            const sample = event[Math.floor(event.length / 2)];
            
            if (!sample.file_path || !fs.existsSync(sample.file_path)) {
                continue;
            }
            
            process.stdout.write(`[${i + 1}/${eventsToProcess.length}] ${sample.filename} (${event.length} fotos)... `);
            
            const visionResult = await callAnalyzeImage(sample.file_path);
            
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
                console.log(`✗ Error`);
            }
            
            // Small delay
            await new Promise(r => setTimeout(r, 200));
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
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
        console.error(error.stack);
    } finally {
        await db.close();
    }
}

efficientAnalyze();
