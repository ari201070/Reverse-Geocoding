// step1-group-events.js - Paso 1: Agrupar fotos en eventos de 60 minutos
// Ejecutar con: node step1-group-events.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const EVENT_WINDOW_MS = 60 * 60 * 1000; // 60 minutes

async function groupEvents() {
    console.log('=== STEP 1: AGRUPAR FOTOS EN EVENTOS DE 60 MINUTOS ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // Get all photos without GPS, ordered by date
        const blindPhotos = await db.all(`
            SELECT id, file_path, filename, date_taken, 
                   CASE 
                       WHEN file_path LIKE 'F:%' THEN 'F:'
                       WHEN file_path LIKE 'G:%' THEN 'G:'
                       ELSE 'Other'
                   END as drive
            FROM photos 
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
            ORDER BY date_taken
        `);
        
        console.log(`Total fotos sin GPS: ${blindPhotos.length}\n`);
        
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
        
        console.log(`Eventos generados: ${events.length}\n`);
        
        // Analyze event distribution
        const eventStats = events.map((e, i) => ({
            index: i,
            count: e.length,
            startDate: e[0].date_taken,
            endDate: e[e.length - 1].date_taken,
            drive: e[0].drive,
            sampleFile: e[0].file_path
        }));
        
        // Sort by count (largest events first)
        eventStats.sort((a, b) => b.count - a.count);
        
        console.log('=== TOP 20 EVENTOS POR TAMAÑO ===');
        for (const e of eventStats.slice(0, 20)) {
            console.log(`Evento ${e.index + 1}: ${e.count} fotos | ${e.startDate} → ${e.endDate} | ${e.drive}`);
        }
        
        // Save events to JSON
        const outputPath = join(__dirname, 'events-grouped.json');
        fs.writeFileSync(outputPath, JSON.stringify({
            totalPhotos: blindPhotos.length,
            totalEvents: events.length,
            events: eventStats
        }, null, 2));
        
        console.log(`\nEventos guardados en: ${outputPath}`);
        
        // Summary by drive
        const byDrive = {};
        for (const e of eventStats) {
            if (!byDrive[e.drive]) byDrive[e.drive] = { events: 0, photos: 0 };
            byDrive[e.drive].events++;
            byDrive[e.drive].photos += e.count;
        }
        
        console.log('\n=== RESUMEN POR DRIVE ===');
        for (const [drive, stats] of Object.entries(byDrive)) {
            console.log(`${drive}: ${stats.events} eventos, ${stats.photos} fotos`);
        }
        
        console.log('\n✅ STEP 1 COMPLETADO');
        console.log('\nPróximo paso: node step2-sample-analyze.js');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
        console.error(error.stack);
    } finally {
        await db.close();
    }
}

groupEvents();
