// enrich-by-location-name.js - Propagate GPS by matching location names
// Ejecutar con: node enrich-by-location-name.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');

function roundCoord(val) {
    if (val === null || val === undefined) return null;
    return Math.round(val * 10000) / 10000;
}

async function enrichByLocationName() {
    console.log('=== ENRICH BY LOCATION NAME ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // 1. Get all unique location names with GPS (anchors)
        console.log('[1/3] Construyendo índice de ubicaciones...');
        
        const anchorLocations = await db.all(`
            SELECT location_name, 
                   AVG(latitude) as avg_lat, 
                   AVG(longitude) as avg_lng,
                   COUNT(*) as cnt
            FROM photos 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
              AND location_name IS NOT NULL AND location_name != ''
              AND abs(latitude) > 0.001
            GROUP BY location_name
            HAVING cnt >= 3
            ORDER BY cnt DESC
        `);
        
        console.log(`    ${anchorLocations.length} ubicaciones con GPS\n`);
        
        // 2. Find photos without GPS but with matching location name
        console.log('[2/3] Buscando fotos sin GPS con ubicaciones conocidas...\n');
        
        let enriched = 0;
        const enrichedByLocation = {};
        
        const updateStmt = await db.prepare(`
            UPDATE photos 
            SET latitude = ?, longitude = ?, 
                date_source = 'LOCATION_NAME_MATCH'
            WHERE id = ?
        `);
        
        for (const loc of anchorLocations) {
            // Find photos with this location name but no GPS
            const photos = await db.all(`
                SELECT id, filename, location_name
                FROM photos 
                WHERE location_name = ?
                  AND (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
            `, [loc.location_name]);
            
            if (photos.length > 0) {
                for (const photo of photos) {
                    await updateStmt.run(
                        roundCoord(loc.avg_lat),
                        roundCoord(loc.avg_lng),
                        photo.id
                    );
                    enriched++;
                }
                
                enrichedByLocation[loc.location_name] = photos.length;
                console.log(`    ${loc.location_name}: +${photos.length} fotos`);
            }
        }
        
        // 3. Report
        console.log('\n[3/3] Reporte...\n');
        
        const stats = await db.get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND abs(latitude) > 0.001 THEN 1 ELSE 0 END) as with_gps
            FROM photos
        `);
        
        console.log('=== REPORTE ===');
        console.log(`Fotos enriquecidas: ${enriched}`);
        console.log(`Total con GPS: ${stats.with_gps} (${((stats.with_gps/stats.total)*100).toFixed(1)}%)`);
        
        if (Object.keys(enrichedByLocation).length > 0) {
            console.log('\n--- Por ubicación ---');
            for (const [loc, cnt] of Object.entries(enrichedByLocation)) {
                console.log(`  ${loc}: +${cnt}`);
            }
        }
        
        console.log('\n✅ COMPLETADO');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
    } finally {
        await db.close();
    }
}

enrichByLocationName();
