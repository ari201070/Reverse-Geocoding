// surgical-sampling.js - Selección quirúrgica de 5 clusters ciegos + análisis + propagación
// Ejecutar con: node surgical-sampling.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const EVENT_WINDOW_MS = 60 * 60 * 1000; // 60 min cluster window
const INHERIT_WINDOW_MS = 15 * 60 * 1000; // 15 min heritage window
const SERVER_URL = 'http://localhost:3000';

function roundCoord(val) {
    if (val === null || val === undefined) return null;
    return Math.round(val * 10000) / 10000;
}

async function callAnalyzeImage(imagePath) {
    try {
        const imageData = fs.readFileSync(imagePath);
        const base64 = imageData.toString('base64');
        
        const res = await fetch(`${SERVER_URL}/api/analyze-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_base64: base64,
                current_step: 'SURGICAL_SAMPLING',
                mime_type: 'image/jpeg'
            }),
            signal: AbortSignal.timeout(120000) // 2 min timeout
        });
        
        if (res.ok) {
            return await res.json();
        } else {
            console.log(`    HTTP ${res.status}`);
        }
    } catch (e) {
        console.log(`    Error: ${e.message}`);
    }
    return null;
}

async function surgicalSampling() {
    console.log('=== SURGICAL SAMPLING: 5 CLUSTERS → ANÁLISIS → PROPAGACIÓN ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // STEP 1: Find blind clusters (photos without GPS, grouped by 60-min windows)
        console.log('[STEP 1] Identificando clusters ciegos...\n');
        
        const blindPhotos = await db.all(`
            SELECT id, file_path, filename, date_taken, 
                   (SELECT COUNT(*) FROM photos p2 
                    WHERE p2.file_path LIKE '%' || SUBSTR(p1.file_path, 1, INSTR(p1.file_path, '/') - 1) || '%'
                      AND p2.latitude IS NOT NULL AND p2.longitude IS NOT NULL
                      AND abs(p2.latitude) > 0.001) as gps_siblings
            FROM photos p1
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
              AND file_path LIKE 'F:%'
            ORDER BY date_taken
        `);
        
        // Group into clusters by 60-min windows
        const clusters = [];
        let currentCluster = [];
        let lastTs = null;
        
        for (const photo of blindPhotos) {
            const ts = new Date(photo.date_taken).getTime();
            if (lastTs === null || (ts - lastTs) > EVENT_WINDOW_MS) {
                if (currentCluster.length > 0) {
                    clusters.push(currentCluster);
                }
                currentCluster = [photo];
            } else {
                currentCluster.push(photo);
            }
            lastTs = ts;
        }
        if (currentCluster.length > 0) {
            clusters.push(currentCluster);
        }
        
        // Filter: only clusters with 0 GPS siblings (completely blind)
        const blindClusters = clusters.filter(c => c.every(p => p.gps_siblings === 0));
        
        // Sort by size (largest first)
        blindClusters.sort((a, b) => b.length - a.length);
        
        console.log(`    Total clusters ciegos (0% GPS): ${blindClusters.length}`);
        console.log(`    Top 5 clusters seleccionados:\n`);
        
        const top5 = blindClusters.slice(0, 5);
        for (let i = 0; i < top5.length; i++) {
            const c = top5[i];
            console.log(`    Cluster ${i+1}: ${c.length} fotos | ${c[0].date_taken} → ${c[c.length-1].date_taken}`);
        }
        
        // STEP 2: Select best photo from each cluster
        console.log('\n[STEP 2] Seleccionando mejor foto de cada cluster...\n');
        
        const selectedPhotos = [];
        
        for (let i = 0; i < top5.length; i++) {
            const cluster = top5[i];
            
            // Sort by file size (largest first), then by name hints
            const withSize = cluster.map(p => {
                let size = 0;
                try {
                    if (p.file_path && fs.existsSync(p.file_path)) {
                        size = fs.statSync(p.file_path).size;
                    }
                } catch(e) {}
                
                // Bonus for sign/ticket-like names
                const nameLower = (p.filename || '').toLowerCase();
                const isSign = nameLower.includes('cartel') || nameLower.includes('ticket') ||
                              nameLower.includes('sign') || nameLower.includes('menu') ||
                              nameLower.includes('foto') || nameLower.includes('img');
                
                return { ...p, size, isSign };
            });
            
            // Prefer signs/tickets, then largest file
            withSize.sort((a, b) => {
                if (a.isSign !== b.isSign) return b.isSign - a.isSign;
                return b.size - a.size;
            });
            
            const best = withSize[0];
            selectedPhotos.push(best);
            
            console.log(`    Cluster ${i+1}: ${best.filename} (${(best.size/1024).toFixed(0)}KB)`);
        }
        
        // STEP 3: Send to analyze-image.js
        console.log('\n[STEP 3] Analizando fotos con api/analyze-image.js...\n');
        
        const analysisResults = [];
        
        for (let i = 0; i < selectedPhotos.length; i++) {
            const photo = selectedPhotos[i];
            console.log(`    [${i+1}/5] ${photo.filename}...`);
            
            if (!photo.file_path || !fs.existsSync(photo.file_path)) {
                console.log(`        ✗ Archivo no encontrado`);
                continue;
            }
            
            const result = await callAnalyzeImage(photo.file_path);
            
            if (result) {
                analysisResults.push({ photo, result });
                console.log(`        ✓ Labels: ${(result.labels || []).slice(0, 3).join(', ')}`);
                console.log(`          Landmarks: ${(result.landmarks || []).join(', ') || 'ninguno'}`);
                console.log(`          Texts: ${(result.texts || []).slice(0, 2).join(' | ') || 'ninguno'}`);
            } else {
                console.log(`        ✗ Sin resultado`);
            }
        }
        
        console.log(`\n    Análisis completados: ${analysisResults.length}/5\n`);
        
        // STEP 4: For each successful analysis, use POI to get coordinates and propagate
        console.log('[STEP 4] Buscando coordenadas y propagando...\n');
        
        let totalEnriched = 0;
        const enrichmentReport = [];
        
        const updateStmt = await db.prepare(`
            UPDATE photos 
            SET latitude = ?, longitude = ?, 
                location_name = ?, city = ?, country = ?,
                date_source = 'SURGICAL_SAMPLING'
            WHERE id = ?
        `);
        
        for (const { photo, result } of analysisResults) {
            // Find the cluster this photo belongs to
            const cluster = top5.find(c => c.some(p => p.id === photo.id));
            if (!cluster) continue;
            
            // Try to find POI from landmarks or texts
            let poiName = null;
            if (result.landmarks && result.landmarks.length > 0) {
                poiName = result.landmarks[0];
            } else if (result.texts && result.texts.length > 0) {
                // Use first meaningful text
                const meaningful = result.texts.find(t => t.length > 3 && !t.match(/^\d+$/));
                if (meaningful) poiName = meaningful;
            }
            
            if (poiName) {
                // Search for POI coordinates
                console.log(`    Buscando POI: "${poiName}"...`);
                
                try {
                    const poiRes = await fetch(`${SERVER_URL}/api/find-poi`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            query: poiName,
                            location: { lat: -34.6037, lng: -58.3816 } // Default: Buenos Aires
                        }),
                        signal: AbortSignal.timeout(30000)
                    });
                    
                    if (poiRes.ok) {
                        const poiData = await poiRes.json();
                        
                        if (poiData && poiData.lat && poiData.lng) {
                            console.log(`        ✓ POI encontrado: ${poiData.name || poiName} (${poiData.lat}, ${poiData.lng})`);
                            
                            // Propagate to all photos in cluster
                            let clusterEnriched = 0;
                            for (const clusterPhoto of cluster) {
                                await updateStmt.run(
                                    roundCoord(poiData.lat),
                                    roundCoord(poiData.lng),
                                    poiData.name || poiName,
                                    poiData.city || '',
                                    poiData.country || '',
                                    clusterPhoto.id
                                );
                                clusterEnriched++;
                            }
                            
                            totalEnriched += clusterEnriched;
                            enrichmentReport.push({
                                cluster: top5.indexOf(cluster) + 1,
                                photo: photo.filename,
                                poi: poiName,
                                coords: `${poiData.lat}, ${poiData.lng}`,
                                enriched: clusterEnriched
                            });
                        }
                    }
                } catch (e) {
                    console.log(`        ✗ Error POI: ${e.message}`);
                }
            } else {
                console.log(`    ✗ No se detectó POI para propagar`);
            }
        }
        
        // STEP 5: Report
        console.log('\n[STEP 5] Reporte final...\n');
        
        const stats = await db.get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND abs(latitude) > 0.001 THEN 1 ELSE 0 END) as with_gps
            FROM photos
        `);
        
        console.log('=== REPORTE SURGICAL SAMPLING ===');
        console.log(`Clusters analizados: 5`);
        console.log(`Fotos analizadas: ${analysisResults.length}`);
        console.log(`Fotos totales enriquecidas: ${totalEnriched}`);
        console.log(`\nTotal fotos con GPS: ${stats.with_gps} (${((stats.with_gps/stats.total)*100).toFixed(1)}%)`);
        
        if (enrichmentReport.length > 0) {
            console.log('\n--- Detalle por cluster ---');
            for (const r of enrichmentReport) {
                console.log(`  Cluster ${r.cluster}: ${r.poi} → ${r.enriched} fotos (${r.coords})`);
            }
        }
        
        console.log('\n✅ SURGICAL SAMPLING COMPLETADO');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
        console.error(error.stack);
    } finally {
        await db.close();
    }
}

surgicalSampling();
