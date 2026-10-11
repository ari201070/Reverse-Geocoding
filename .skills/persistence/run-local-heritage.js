// run-local-heritage.js - Paso 7: Heritage - Propagación local determinista
// Ejecutar con: node run-local-heritage.js

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

async function runLocalHeritage() {
    console.log('=== PASO 7: HERITAGE - PROPAGACIÓN LOCAL DETERMINISTA ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // 1. Buscar fotos ancla válidas (con GPS + location_name + city + country)
        console.log('[1/5] Buscando fotos ancla válidas...');
        const anchors = await db.all(`
            SELECT id, file_path, filename, date_taken, 
                   latitude, longitude, location_name, city, country
            FROM photos 
            WHERE latitude IS NOT NULL 
              AND longitude IS NOT NULL
              AND location_name IS NOT NULL 
              AND location_name != ''
              AND city IS NOT NULL
              AND country IS NOT NULL
              AND abs(latitude) > 0.001
              AND abs(longitude) > 0.001
              AND date_taken IS NOT NULL
              AND date_taken != ''
            ORDER BY date_taken
        `);
        
        console.log(`    Encontradas ${anchors.length} fotos ancla con GPS y metadata completa`);
        
        if (anchors.length === 0) {
            console.log('No hay fotos ancla válidas. Abortando.');
            return;
        }

        // 2. Buscar fotos candidatas sin GPS
        console.log('\n[2/5] Buscando fotos candidatas sin GPS...');
        const candidates = await db.all(`
            SELECT id, file_path, filename, date_taken, latitude, longitude
            FROM photos 
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
            ORDER BY date_taken
        `);
        
        console.log(`    Encontradas ${candidates.length} fotos sin GPS con fecha válida`);
        
        if (candidates.length === 0) {
            console.log('No hay fotos candidatas. Nada que propagar.');
            return;
        }

        // 3. Para cada candidato, buscar si hay un ancla dentro de ±15 min
        console.log('\n[3/5] Propagando metadatos por proximidad temporal...');
        
        let enriched = 0;
        const enrichedDetails = [];
        const enrichedIds = new Set();
        
        const updateStmt = await db.prepare(`
            UPDATE photos 
            SET latitude = ?, longitude = ?, 
                location_name = ?, city = ?, country = ?,
                date_source = 'HERITAGE_PROPAGATION'
            WHERE id = ?
        `);
        
        for (const cand of candidates) {
            if (enrichedIds.has(cand.id)) continue;
            
            const candTs = new Date(cand.date_taken).getTime();
            
            // Buscar ancla más cercana dentro de ±15 min
            let bestAnchor = null;
            let bestTimeDiff = Infinity;
            
            for (const anchor of anchors) {
                const anchorTs = new Date(anchor.date_taken).getTime();
                const timeDiff = Math.abs(candTs - anchorTs);
                
                if (timeDiff <= INHERIT_WINDOW_MS && timeDiff < bestTimeDiff) {
                    bestTimeDiff = timeDiff;
                    bestAnchor = anchor;
                }
            }
            
            if (bestAnchor) {
                await updateStmt.run(
                    roundCoord(bestAnchor.latitude),
                    roundCoord(bestAnchor.longitude),
                    bestAnchor.location_name,
                    bestAnchor.city,
                    bestAnchor.country,
                    cand.id
                );
                
                enriched++;
                enrichedIds.add(cand.id);
                enrichedDetails.push({
                    targetId: cand.id,
                    targetFile: cand.filename,
                    targetDate: cand.date_taken,
                    anchorId: bestAnchor.id,
                    anchorFile: bestAnchor.filename,
                    anchorDate: bestAnchor.date_taken,
                    anchorLocation: bestAnchor.location_name,
                    timeDiffMin: Math.round(bestTimeDiff / 60000)
                });
            }
        }
        
        // 4. Reporte de impacto
        console.log('\n[4/5] Generando reporte de impacto...\n');
        
        const stats = await db.get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND abs(latitude) > 0.001 THEN 1 ELSE 0 END) as with_gps,
                SUM(CASE WHEN latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0 THEN 1 ELSE 0 END) as without_gps
            FROM photos
        `);
        
        console.log('=== REPORTE DE IMPACTO - PASO 7 HERITAGE ===');
        console.log(`Fotos ancla de origen:     ${anchors.length}`);
        console.log(`Fotos enriquecidas:        ${enriched}`);
        console.log(`Total fotos en catálogo:   ${stats.total}`);
        console.log(`Fotos con GPS:             ${stats.with_gps} (${((stats.with_gps/stats.total)*100).toFixed(1)}%)`);
        console.log(`Fotos sin GPS restantes:   ${stats.without_gps} (${((stats.without_gps/stats.total)*100).toFixed(1)}%)`);
        console.log(`Avance hacia meta (100% GPS): ${((stats.with_gps/stats.total)*100).toFixed(1)}%`);
        
        if (enrichedDetails.length > 0) {
            console.log('\n--- Detalle de enriquecimientos ---');
            for (const d of enrichedDetails.slice(0, 20)) {
                console.log(`  ID ${d.targetId} (${d.targetFile}) <- ID ${d.anchorId} (${d.anchorFile})`);
                console.log(`    ${d.targetDate} -> ${d.anchorLocation} (Δt: ${d.timeDiffMin}min)`);
            }
            if (enrichedDetails.length > 20) {
                console.log(`    ... y ${enrichedDetails.length - 20} más`);
            }
        }
        
        console.log('\n✅ PASO 7 COMPLETADO - Propagación local determinista finalizada');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
        console.error(error.stack);
    } finally {
        await db.close();
    }
}

runLocalHeritage();
