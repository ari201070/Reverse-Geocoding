// fix-heic-dates-and-enrich.js - Fix HEIC photos: extract dates from filenames, propagate GPS
// Ejecutar con: node fix-heic-dates-and-enrich.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');

function extractDateFromFilename(filename) {
    // Pattern: 20250927_213136.heic -> 2025-09-27 21:31:36
    const match = filename.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
    if (match) {
        const [_, year, month, day, hour, min, sec] = match;
        return `${year}-${month}-${day} ${hour}:${min}:${sec}`;
    }
    return null;
}

async function fixAndEnrich() {
    console.log('=== FIX HEIC DATES & ENRICH ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // 1. Find photos without date_taken
        console.log('[1/3] Buscando fotos sin date_taken...');
        const noDatePhotos = await db.all(`
            SELECT id, filename, file_path, location_name, city, country
            FROM photos 
            WHERE (date_taken IS NULL OR date_taken = '')
              AND location_name IS NOT NULL
              AND location_name != ''
        `);
        console.log(`    ${noDatePhotos.length} fotos sin fecha\n`);
        
        // 2. Extract dates from filenames and update
        console.log('[2/3] Extrayendo fechas de filenames...');
        
        let datesFixed = 0;
        const updateDateStmt = await db.prepare(`
            UPDATE photos SET date_taken = ? WHERE id = ?
        `);
        
        for (const photo of noDatePhotos) {
            const date = extractDateFromFilename(photo.filename);
            if (date) {
                await updateDateStmt.run(date, photo.id);
                datesFixed++;
            }
        }
        console.log(`    ${datesFixed} fechas actualizadas\n`);
        
        // 3. Now propagate GPS using date_taken
        console.log('[3/3] Propagando GPS por proximidad temporal...');
        
        // Get updated photos without GPS
        const photosNeedingGPS = await db.all(`
            SELECT id, filename, date_taken, location_name, city, country
            FROM photos 
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
              AND location_name IS NOT NULL
              AND location_name != ''
        `);
        
        // Get anchors with GPS
        const anchors = await db.all(`
            SELECT id, filename, date_taken, latitude, longitude, location_name
            FROM photos 
            WHERE latitude IS NOT NULL 
              AND longitude IS NOT NULL
              AND location_name IS NOT NULL 
              AND location_name != ''
              AND abs(latitude) > 0.001
              AND abs(longitude) > 0.001
            ORDER BY date_taken
        `);
        
        console.log(`    Fotos sin GPS: ${photosNeedingGPS.length}`);
        console.log(`    Fotos ancla: ${anchors.length}\n`);
        
        let enriched = 0;
        const updateGPSStmt = await db.prepare(`
            UPDATE photos 
            SET latitude = ?, longitude = ?, 
                date_source = 'HEIC_PROPAGATION'
            WHERE id = ?
        `);
        
        for (const photo of photosNeedingGPS) {
            const photoTs = new Date(photo.date_taken).getTime();
            
            // Find closest anchor within 15 min
            let bestAnchor = null;
            let bestTimeDiff = Infinity;
            
            for (const anchor of anchors) {
                const anchorTs = new Date(anchor.date_taken).getTime();
                const timeDiff = Math.abs(photoTs - anchorTs);
                
                if (timeDiff <= 15 * 60 * 1000 && timeDiff < bestTimeDiff) {
                    bestTimeDiff = timeDiff;
                    bestAnchor = anchor;
                }
            }
            
            if (bestAnchor) {
                await updateGPSStmt.run(
                    Math.round(bestAnchor.latitude * 10000) / 10000,
                    Math.round(bestAnchor.longitude * 10000) / 10000,
                    photo.id
                );
                enriched++;
            }
        }
        
        // Final stats
        const stats = await db.get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND abs(latitude) > 0.001 THEN 1 ELSE 0 END) as with_gps
            FROM photos
        `);
        
        console.log('\n=== REPORTE FINAL ===');
        console.log(`Fechas corregidas: ${datesFixed}`);
        console.log(`Fotos enriquecidas con GPS: ${enriched}`);
        console.log(`Total fotos con GPS: ${stats.with_gps} (${((stats.with_gps/stats.total)*100).toFixed(1)}%)`);
        
        console.log('\n✅ COMPLETADO');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
    } finally {
        await db.close();
    }
}

fixAndEnrich();
