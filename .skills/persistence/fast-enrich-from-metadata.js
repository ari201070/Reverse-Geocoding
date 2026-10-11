// fast-enrich-from-metadata.js - Enriquecimiento rápido usando metadatos existentes
// NO usa Ollama - solo SQL y lógica local
// Ejecutar con: node fast-enrich-from-metadata.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const INHERIT_WINDOW_MS = 15 * 60 * 1000; // 15 minutes

function roundCoord(val) {
    if (val === null || val === undefined) return null;
    return Math.round(val * 10000) / 10000;
}

async function fastEnrich() {
    console.log('=== FAST ENRICH: METADATA-BASED ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // 1. Find photos that already have location info from folder names
        console.log('[1/4] Buscando fotos con info de carpetas...');
        const folderEnriched = await db.all(`
            SELECT id, file_path, filename, date_taken, location_name, city, country
            FROM photos 
            WHERE location_name IS NOT NULL 
              AND location_name != ''
              AND city IS NOT NULL
              AND country IS NOT NULL
              AND (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
        `);
        console.log(`    ${folderEnriched.length} fotos con location_name pero sin GPS`);
        
        // 2. Find anchor photos with GPS + location
        console.log('\n[2/4] Buscando fotos ancla...');
        const anchors = await db.all(`
            SELECT id, file_path, filename, date_taken, 
                   latitude, longitude, location_name, city, country
            FROM photos 
            WHERE latitude IS NOT NULL 
              AND longitude IS NOT NULL
              AND location_name IS NOT NULL 
              AND location_name != ''
              AND abs(latitude) > 0.001
              AND abs(longitude) > 0.001
            ORDER BY date_taken
        `);
        console.log(`    ${anchors.length} fotos ancla con GPS y metadata`);
        
        // 3. For each folder-enriched photo, find closest anchor by time
        console.log('\n[3/4] Propagando GPS por proximidad temporal...');
        
        let enriched = 0;
        const enrichedDetails = [];
        
        const updateStmt = await db.prepare(`
            UPDATE photos 
            SET latitude = ?, longitude = ?, 
                date_source = 'FOLDER_PROPAGATION'
            WHERE id = ?
        `);
        
        for (const photo of folderEnriched) {
            const photoTs = new Date(photo.date_taken).getTime();
            
            // Find closest anchor within 15 min
            let bestAnchor = null;
            let bestTimeDiff = Infinity;
            
            for (const anchor of anchors) {
                const anchorTs = new Date(anchor.date_taken).getTime();
                const timeDiff = Math.abs(photoTs - anchorTs);
                
                if (timeDiff <= INHERIT_WINDOW_MS && timeDiff < bestTimeDiff) {
                    bestTimeDiff = timeDiff;
                    bestAnchor = anchor;
                }
            }
            
            if (bestAnchor) {
                await updateStmt.run(
                    roundCoord(bestAnchor.latitude),
                    roundCoord(bestAnchor.longitude),
                    photo.id
                );
                
                enriched++;
                enrichedDetails.push({
                    targetId: photo.id,
                    targetFile: photo.filename,
                    anchorId: bestAnchor.id,
                    anchorFile: bestAnchor.filename,
                    location: photo.location_name,
                    timeDiffMin: Math.round(bestTimeDiff / 60000)
                });
            }
        }
        
        // 4. Report
        console.log('\n[4/4] Generando reporte...\n');
        
        const stats = await db.get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND abs(latitude) > 0.001 THEN 1 ELSE 0 END) as with_gps
            FROM photos
        `);
        
        console.log('=== REPORTE ===');
        console.log(`Fotos con location_name sin GPS: ${folderEnriched.length}`);
        console.log(`Fotos ancla disponibles: ${anchors.length}`);
        console.log(`Fotos enriquecidas: ${enriched}`);
        console.log(`Total fotos con GPS: ${stats.with_gps} (${((stats.with_gps/stats.total)*100).toFixed(1)}%)`);
        
        if (enrichedDetails.length > 0) {
            console.log('\n--- Muestra de enriquecimientos ---');
            for (const d of enrichedDetails.slice(0, 10)) {
                console.log(`  ${d.targetFile} -> ${d.location} (Δt: ${d.timeDiffMin}min)`);
            }
        }
        
        console.log('\n✅ COMPLETADO');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
    } finally {
        await db.close();
    }
}

fastEnrich();
