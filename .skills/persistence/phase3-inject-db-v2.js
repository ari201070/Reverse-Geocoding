// phase3-inject-db-v2.js - Fixed: match by month folder
// Ejecutar con: node phase3-inject-db-v2.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const INHERIT_WINDOW_MS = 15 * 60 * 1000;

function roundCoord(val) {
    if (val === null || val === undefined) return null;
    return Math.round(val * 10000) / 10000;
}

async function phase3Inject() {
    console.log('=== FASE 3: INYECCIÓN EN DB (v2) ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // 1. Load folder-anchors.json
        const folderData = JSON.parse(readFileSync(join(__dirname, 'api', 'folder-anchors.json'), 'utf8'));
        
        // Filter only folders with coordinates
        const geocodedFolders = Object.entries(folderData).filter(
            ([_, data]) => data.lat !== null && data.lng !== null
        );
        
        console.log(`Carpetas geocodificadas: ${geocodedFolders.length}\n`);
        
        // 2. For each geocoded folder, update first photo
        let injected = 0;
        let skipped = 0;
        const updateStmt = await db.prepare(`
            UPDATE photos 
            SET latitude = ?, longitude = ?, 
                location_name = ?, city = ?, country = ?,
                date_source = 'HEURISTICA_CARPETA'
            WHERE id = ?
        `);
        
        for (const [folder, data] of geocodedFolders) {
            // Extract year and month from folder path
            // e.g., "F:\2011\Noviembre" -> year=2011, month=Noviembre
            const folderParts = folder.replace(/\\/g, '/').split('/');
            const year = folderParts.find(p => /^\d{4}$/.test(p));
            const month = folderParts.find(p => /^[A-Z]/.test(p) && p.length > 2 && !/^\d+$/.test(p));
            
            if (!year || !month) {
                skipped++;
                continue;
            }
            
            // Find first photo in this year/month folder
            const firstPhoto = await db.get(`
                SELECT id, filename, file_path
                FROM photos
                WHERE file_path LIKE ?
                  AND (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
                ORDER BY date_taken ASC
                LIMIT 1
            `, [`%${year}\\${month}%`]);
            
            if (firstPhoto) {
                const parts = (data.location_name || '').split(',').map(s => s.trim());
                
                await updateStmt.run(
                    roundCoord(data.lat),
                    roundCoord(data.lng),
                    data.name,
                    parts[0] || '',
                    parts[1] || '',
                    firstPhoto.id
                );
                injected++;
            } else {
                skipped++;
            }
        }
        
        console.log(`Fotos inyectadas: ${injected}`);
        console.log(`Carpetas sin fotos: ${skipped}\n`);
        
        // 3. FASE 4: Heritage propagation
        console.log('=== FASE 4: HERITAGE PROPAGATION ===\n');
        
        // Get all anchors
        const anchors = await db.all(`
            SELECT id, date_taken, latitude, longitude, location_name, city, country, file_path
            FROM photos
            WHERE date_source = 'HEURISTICA_CARPETA'
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
            ORDER BY date_taken
        `);
        
        console.log(`Anclas HEURISTICA_CARPETA: ${anchors.length}\n`);
        
        if (anchors.length === 0) {
            console.log('No hay anclas. Abortando Heritage.');
            return;
        }
        
        // Get all photos without GPS
        const blindPhotos = await db.all(`
            SELECT id, date_taken, file_path
            FROM photos
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
            ORDER BY date_taken
        `);
        
        console.log(`Fotos ciegas: ${blindPhotos.length}\n`);
        
        let propagated = 0;
        const propagateStmt = await db.prepare(`
            UPDATE photos
            SET latitude = ?, longitude = ?,
                location_name = ?, city = ?, country = ?,
                date_source = 'HERITAGE_FROM_CARPETA'
            WHERE id = ?
        `);
        
        // For each blind photo, find closest anchor
        for (const photo of blindPhotos) {
            const photoTs = new Date(photo.date_taken).getTime();
            const photoFolder = photo.file_path.replace(/\\/g, '/').substring(0, photo.file_path.replace(/\\/g, '/').lastIndexOf('/'));
            
            let bestAnchor = null;
            let bestDiff = Infinity;
            
            for (const anchor of anchors) {
                const anchorTs = new Date(anchor.date_taken).getTime();
                const diff = Math.abs(photoTs - anchorTs);
                const anchorFolder = anchor.file_path.replace(/\\/g, '/').substring(0, anchor.file_path.replace(/\\/g, '/').lastIndexOf('/'));
                
                // Same folder: larger window (60 min)
                // Different folder: smaller window (15 min)
                const window = photoFolder === anchorFolder ? 60 * 60 * 1000 : INHERIT_WINDOW_MS;
                
                if (diff <= window && diff < bestDiff) {
                    bestDiff = diff;
                    bestAnchor = anchor;
                }
            }
            
            if (bestAnchor) {
                await propagateStmt.run(
                    roundCoord(bestAnchor.latitude),
                    roundCoord(bestAnchor.longitude),
                    bestAnchor.location_name,
                    bestAnchor.city,
                    bestAnchor.country,
                    photo.id
                );
                propagated++;
            }
        }
        
        console.log(`Fotos propagadas por Heritage: ${propagated}\n`);
        
        // 4. Final stats
        const stats = await db.get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND abs(latitude) > 0.001 THEN 1 ELSE 0 END) as with_gps,
                SUM(CASE WHEN date_source = 'HEURISTICA_CARPETA' THEN 1 ELSE 0 END) as heuristica,
                SUM(CASE WHEN date_source = 'HERITAGE_FROM_CARPETA' THEN 1 ELSE 0 END) as heritage_carpeta
            FROM photos
        `);
        
        console.log('=== REPORTE FINAL ===');
        console.log(`Total fotos: ${stats.total}`);
        console.log(`Con GPS: ${stats.with_gps} (${((stats.with_gps/stats.total)*100).toFixed(1)}%)`);
        console.log(`HEURISTICA_CARPETA: ${stats.heuristica}`);
        console.log(`HERITAGE_FROM_CARPETA: ${stats.heritage_carpeta}`);
        console.log(`Total enriquecidas sesión: ${(stats.heuristica||0) + (stats.heritage_carpeta||0)}`);
        
        console.log('\n✅ FASE 3+4 COMPLETADAS');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
        console.error(error.stack);
    } finally {
        await db.close();
    }
}

phase3Inject();
