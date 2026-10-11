// surgical-sampling-fast.js - Simplified surgical sampling
// Ejecutar con: node surgical-sampling-fast.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const EVENT_WINDOW_MS = 60 * 60 * 1000;
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
            signal: AbortSignal.timeout(120000)
        });
        
        if (res.ok) return await res.json();
    } catch (e) {
        console.log(`    Error: ${e.message}`);
    }
    return null;
}

async function surgicalSampling() {
    console.log('=== SURGICAL SAMPLING: 5 CLUSTERS → ANÁLISIS → PROPAGACIÓN ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // STEP 1: Get blind photos from F: drive with dates
        console.log('[STEP 1] Buscando fotos ciegas...\n');
        
        const blindPhotos = await db.all(`
            SELECT id, file_path, filename, date_taken
            FROM photos 
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
              AND file_path LIKE 'F:%'
            ORDER BY date_taken
        `);
        
        console.log(`    ${blindPhotos.length} fotos ciegas en F: drive\n`);
        
        // Group into 60-min clusters
        const clusters = [];
        let currentCluster = [];
        let lastTs = null;
        
        for (const photo of blindPhotos) {
            const ts = new Date(photo.date_taken).getTime();
            if (lastTs === null || (ts - lastTs) > EVENT_WINDOW_MS) {
                if (currentCluster.length > 0) clusters.push(currentCluster);
                currentCluster = [photo];
            } else {
                currentCluster.push(photo);
            }
            lastTs = ts;
        }
        if (currentCluster.length > 0) clusters.push(currentCluster);
        
        // Sort by size, take top 5
        clusters.sort((a, b) => b.length - a.length);
        const top5 = clusters.slice(0, 5);
        
        console.log('    Top 5 clusters ciegos:');
        for (let i = 0; i < top5.length; i++) {
            console.log(`    ${i+1}. ${top5[i].length} fotos | ${top5[i][0].date_taken}`);
        }
        
        // STEP 2: Select best photo from each cluster
        console.log('\n[STEP 2] Seleccionando mejores fotos...\n');
        
        const selectedPhotos = [];
        
        for (let i = 0; i < top5.length; i++) {
            const cluster = top5[i];
            
            // Sort by file size
            const withSize = cluster.map(p => {
                let size = 0;
                try {
                    if (p.file_path && fs.existsSync(p.file_path)) {
                        size = fs.statSync(p.file_path).size;
                    }
                } catch(e) {}
                return { ...p, size };
            }).sort((a, b) => b.size - a.size);
            
            selectedPhotos.push(withSize[0]);
            console.log(`    Cluster ${i+1}: ${withSize[0].filename} (${(withSize[0].size/1024).toFixed(0)}KB)`);
        }
        
        // STEP 3: Analyze with vision
        console.log('\n[STEP 3] Analizando con api/analyze-image.js...\n');
        
        const results = [];
        
        for (let i = 0; i < selectedPhotos.length; i++) {
            const photo = selectedPhotos[i];
            console.log(`    [${i+1}/5] ${photo.filename}...`);
            
            if (!photo.file_path || !fs.existsSync(photo.file_path)) {
                console.log(`        ✗ No encontrado`);
                continue;
            }
            
            const result = await callAnalyzeImage(photo.file_path);
            
            if (result) {
                results.push({ photo, result, cluster: top5[i] });
                console.log(`        ✓ Labels: ${(result.labels || []).slice(0, 3).join(', ')}`);
                console.log(`          Landmarks: ${(result.landmarks || []).join(', ') || '-'}`);
                console.log(`          Texts: ${(result.texts || []).slice(0, 2).join(' | ') || '-'}`);
            } else {
                console.log(`        ✗ Sin resultado`);
            }
        }
        
        console.log(`\n    Analizados: ${results.length}/5\n`);
        
        // STEP 4: Propagate using time-based matching
        console.log('[STEP 4] Propagando por proximidad temporal...\n');
        
        let totalEnriched = 0;
        
        // Get all anchors with GPS
        const anchors = await db.all(`
            SELECT id, date_taken, latitude, longitude, location_name, city, country
            FROM photos 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
              AND location_name IS NOT NULL AND location_name != ''
              AND abs(latitude) > 0.001
            ORDER BY date_taken
        `);
        
        const updateStmt = await db.prepare(`
            UPDATE photos 
            SET latitude = ?, longitude = ?, 
                location_name = ?, city = ?, country = ?,
                date_source = 'SURGICAL_SAMPLING'
            WHERE id = ?
        `);
        
        for (const { cluster } of results) {
            // For each photo in cluster, find closest anchor
            let clusterEnriched = 0;
            
            for (const photo of cluster) {
                const photoTs = new Date(photo.date_taken).getTime();
                
                let bestAnchor = null;
                let bestDiff = Infinity;
                
                for (const anchor of anchors) {
                    const anchorTs = new Date(anchor.date_taken).getTime();
                    const diff = Math.abs(photoTs - anchorTs);
                    
                    if (diff <= 15 * 60 * 1000 && diff < bestDiff) {
                        bestDiff = diff;
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
                        photo.id
                    );
                    clusterEnriched++;
                }
            }
            
            totalEnriched += clusterEnriched;
            console.log(`    Cluster: ${clusterEnriched}/${cluster.length} fotos enriquecidas`);
        }
        
        // Final stats
        const stats = await db.get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND abs(latitude) > 0.001 THEN 1 ELSE 0 END) as with_gps
            FROM photos
        `);
        
        console.log('\n=== REPORTE FINAL ===');
        console.log(`Fotos analizadas: ${results.length}`);
        console.log(`Fotos enriquecidas: ${totalEnriched}`);
        console.log(`Total con GPS: ${stats.with_gps} (${((stats.with_gps/stats.total)*100).toFixed(1)}%)`);
        
        console.log('\n✅ COMPLETADO');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
    } finally {
        await db.close();
    }
}

surgicalSampling();
