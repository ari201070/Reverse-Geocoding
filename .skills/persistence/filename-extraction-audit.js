// filename-extraction-audit.js - Extraer ubicaciones de nombres de archivo
// Ejecutar con: node filename-extraction-audit.js

import { open } from 'sqlite';
import sqlite3 from 'sqlite3';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'photo_catalog.db');
const INHERIT_WINDOW_MS = 15 * 60 * 1000;

function roundCoord(val) {
    if (val === null || val === undefined) return null;
    return Math.round(val * 10000) / 10000;
}

// Location database
const LOCATIONS = {
    // Argentina
    'Lago Puelo': { lat: -41.9539, lng: -71.5564, name: 'Lago Puelo, Argentina' },
    'Gobernador Costa': { lat: -42.5203, lng: -71.3156, name: 'Gobernador Costa, Argentina' },
    'El Bolsón': { lat: -41.9539, lng: -71.5564, name: 'El Bolsón, Argentina' },
    'Los Antiguos': { lat: -46.5432, lng: -71.6318, name: 'Los Antiguos, Argentina' },
    'Perito Moreno': { lat: -49.9333, lng: -73.2000, name: 'Perito Moreno, Argentina' },
    'Calafate': { lat: -50.3364, lng: -72.2646, name: 'El Calafate, Argentina' },
    'Bariloche': { lat: -41.1335, lng: -71.3103, name: 'San Carlos de Bariloche, Argentina' },
    'Villa Traful': { lat: -40.3167, lng: -70.2833, name: 'Villa Traful, Argentina' },
    'Villa La Angostura': { lat: -40.7617, lng: -71.6872, name: 'Villa La Angostura, Argentina' },
    'San Martín de los Andes': { lat: -40.0733, lng: -71.3564, name: 'San Martín de los Andes, Argentina' },
    'Aluminé': { lat: -38.7167, lng: -70.8167, name: 'Aluminé, Argentina' },
    'Zapala': { lat: -38.9000, lng: -70.0667, name: 'Zapala, Argentina' },
    'Neuquén': { lat: -38.9517, lng: -68.0594, name: 'Neuquén, Argentina' },
    'General Roca': { lat: -39.0333, lng: -67.5833, name: 'General Roca, Argentina' },
    'Cipolletti': { lat: -38.9333, lng: -67.9833, name: 'Cipolletti, Argentina' },
    'Viedma': { lat: -40.8133, lng: -62.9967, name: 'Viedma, Argentina' },
    'Carmen de Patagones': { lat: -40.7667, lng: -62.9667, name: 'Carmen de Patagones, Argentina' },
    'Trelew': { lat: -43.2489, lng: -71.3375, name: 'Trelew, Argentina' },
    'Rawson': { lat: -43.2667, lng: -65.1000, name: 'Rawson, Argentina' },
    'Gaiman': { lat: -43.2833, lng: -65.4833, name: 'Gaiman, Argentina' },
    'Trevelin': { lat: -43.0449, lng: -71.3983, name: 'Trevelin, Argentina' },
    'Esquel': { lat: -42.9167, lng: -71.3167, name: 'Esquel, Argentina' },
    'Lago Rivadavia': { lat: -42.0833, lng: -71.3667, name: 'Lago Rivadavia, Argentina' },
    'Cholila': { lat: -42.5167, lng: -71.4333, name: 'Cholila, Argentina' },
    'Cueva de las Manos': { lat: -47.1533, lng: -70.6667, name: 'Cueva de las Manos, Argentina' },
    'Treinta y Tres': { lat: -33.2333, lng: -54.3833, name: 'Treinta y Tres, Uruguay' },
    'Minas': { lat: -34.3667, lng: -55.2333, name: 'Minas, Uruguay' },
    'Piriápolis': { lat: -34.9000, lng: -55.2667, name: 'Piriápolis, Uruguay' },
    'Punta del Este': { lat: -34.9667, lng: -54.9500, name: 'Punta del Este, Uruguay' },
    'Colonia': { lat: -34.4667, lng: -57.8333, name: 'Colonia del Sacramento, Uruguay' },
    'Montevideo': { lat: -34.9011, lng: -56.1645, name: 'Montevideo, Uruguay' },
    
    // Israel
    'ירושלים': { lat: 31.7683, lng: 35.2137, name: 'Jerusalem' },
    'תל אביב': { lat: 32.0853, lng: 34.7818, name: 'Tel Aviv' },
    'חיפה': { lat: 32.7940, lng: 34.9896, name: 'Haifa' },
    'אילת': { lat: 29.5577, lng: 34.9519, name: 'Eilat' },
    'באר שבע': { lat: 31.2530, lng: 34.7915, name: 'Beer Sheva' },
    
    // Europe
    'Bled': { lat: 46.3683, lng: 14.1136, name: 'Bled, Slovenia' },
    'Dubrovnik': { lat: 42.6507, lng: 18.0944, name: 'Dubrovnik, Croatia' },
    'Kotor': { lat: 42.4247, lng: 18.7712, name: 'Kotor, Montenegro' },
    'Budva': { lat: 42.2895, lng: 18.8394, name: 'Budva, Montenegro' },
    'Podgorica': { lat: 42.4304, lng: 19.2594, name: 'Podgorica, Montenegro' },
    'Rome': { lat: 41.9028, lng: 12.4964, name: 'Rome, Italy' },
    'Milano': { lat: 45.4642, lng: 9.1900, name: 'Milan, Italy' },
    'Venezia': { lat: 45.4408, lng: 12.3155, name: 'Venice, Italy' },
    'Firenze': { lat: 43.7696, lng: 11.2558, name: 'Florence, Italy' },
    'Pisa': { lat: 43.7228, lng: 10.4017, name: 'Pisa, Italy' },
    'Barcelona': { lat: 41.3851, lng: 2.1734, name: 'Barcelona, Spain' },
    'Madrid': { lat: 40.4168, lng: -3.7038, name: 'Madrid, Spain' },
    'Lisboa': { lat: 38.7223, lng: -9.1393, name: 'Lisbon, Portugal' },
    'Praha': { lat: 50.0755, lng: 14.4378, name: 'Prague, Czech Republic' },
    'Budapest': { lat: 47.4979, lng: 19.0402, name: 'Budapest, Hungary' },
    'Athens': { lat: 37.9838, lng: 23.7275, name: 'Athens, Greece' },
    'Santorini': { lat: 36.3932, lng: 25.4615, name: 'Santorini, Greece' },
    'Crete': { lat: 35.2401, lng: 24.4691, name: 'Crete, Greece' },
    
    // Spain specific
    'Sevilla': { lat: 37.3891, lng: -5.9845, name: 'Seville, Spain' },
    'Granada': { lat: 37.1773, lng: -3.5986, name: 'Granada, Spain' },
    'Málaga': { lat: 36.7213, lng: -4.4214, name: 'Málaga, Spain' },
    'Valencia': { lat: 39.4699, lng: -0.3763, name: 'Valencia, Spain' },
    'Bilbao': { lat: 43.2630, lng: -2.9350, name: 'Bilbao, Spain' },
    'San Sebastián': { lat: 43.3183, lng: -1.9812, name: 'San Sebastián, Spain' },
    'Zaragoza': { lat: 41.6488, lng: -0.8891, name: 'Zaragoza, Spain' },
    
    // Common patterns
    'Caleta': { lat: -42.0500, lng: -71.5000, name: 'Caleta, Patagonia' },
    'Puerto': { lat: -42.0500, lng: -71.5000, name: 'Puerto, Patagonia' },
    'Lago': { lat: -42.0500, lng: -71.5000, name: 'Lago, Patagonia' },
    'Río': { lat: -42.0500, lng: -71.5000, name: 'Río, Patagonia' },
    'Cerro': { lat: -42.0500, lng: -71.5000, name: 'Cerro, Patagonia' },
    'Bahía': { lat: -42.0500, lng: -71.5000, name: 'Bahía, Patagonia' },
};

// Extract location from filename
function extractLocationFromFilename(filename) {
    if (!filename) return null;
    
    const name = filename
        .replace(/\.[^.]+$/, '') // Remove extension
        .replace(/_/g, ' ') // Replace underscores
        .replace(/-/g, ' '); // Replace dashes
    
    // Pattern 1: Text in parentheses
    const parenMatch = name.match(/\(([^)]+)\)/);
    if (parenMatch) {
        const token = parenMatch[1].trim();
        if (token.length > 2) {
            // Search in locations
            for (const [key, loc] of Object.entries(LOCATIONS)) {
                if (token.toLowerCase().includes(key.toLowerCase()) || 
                    key.toLowerCase().includes(token.toLowerCase())) {
                    return { token, ...loc };
                }
            }
            // Try partial match
            for (const [key, loc] of Object.entries(LOCATIONS)) {
                if (token.toLowerCase().includes(key.toLowerCase().substring(0, 4)) ||
                    key.toLowerCase().includes(token.toLowerCase().substring(0, 4))) {
                    return { token, ...loc };
                }
            }
        }
    }
    
    // Pattern 2: Known location names in filename
    for (const [key, loc] of Object.entries(LOCATIONS)) {
        if (name.toLowerCase().includes(key.toLowerCase())) {
            return { token: key, ...loc };
        }
    }
    
    // Pattern 3: Spanish/Hebrew place patterns
    const placePatterns = [
        /^(Lago|Laguna|Cerro|Río|Rio|Bahía|Bahia|Puerto|Caleta|Isla|Valle|Monte)\s+(.+)/i,
        /^(San|Santa|Santo|Villa|Ciudad)\s+(.+)/i,
    ];
    
    for (const pattern of placePatterns) {
        const match = name.match(pattern);
        if (match) {
            const token = match[0];
            for (const [key, loc] of Object.entries(LOCATIONS)) {
                if (token.toLowerCase().includes(key.toLowerCase())) {
                    return { token, ...loc };
                }
            }
        }
    }
    
    return null;
}

async function filenameExtractionAudit() {
    console.log('=== FILENAME EXTRACTION AUDIT ===\n');
    
    const db = await open({ filename: DB_PATH, driver: sqlite3.Database });
    
    try {
        // 1. Get all blind photos
        const blindPhotos = await db.all(`
            SELECT id, file_path, filename, date_taken
            FROM photos
            WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
              AND date_taken IS NOT NULL
              AND date_taken != ''
            ORDER BY date_taken
        `);
        
        console.log(`Fotos ciegas: ${blindPhotos.length}\n`);
        
        // 2. Extract locations from filenames
        let extracted = 0;
        const extractedLocations = new Map();
        
        for (const photo of blindPhotos) {
            const location = extractLocationFromFilename(photo.filename);
            if (location) {
                extracted++;
                if (!extractedLocations.has(location.token)) {
                    extractedLocations.set(location.token, { ...location, count: 0, photos: [] });
                }
                const loc = extractedLocations.get(location.token);
                loc.count++;
                if (loc.photos.length < 3) {
                    loc.photos.push(photo.filename);
                }
            }
        }
        
        console.log(`Ubicaciones extraídas: ${extractedLocations.size}`);
        console.log(`Fotos con ubicación: ${extracted}\n`);
        
        // 3. Show results
        console.log('--- TOP 20 UBICACIONES EXTRAÍDAS ---');
        const sorted = [...extractedLocations.values()].sort((a, b) => b.count - a.count);
        for (const loc of sorted.slice(0, 20)) {
            console.log(`${loc.token}: ${loc.count} fotos (${loc.lat}, ${loc.lng})`);
            console.log(`  Ejemplos: ${loc.photos.join(', ')}`);
        }
        
        // 4. Inject anchors into DB
        console.log('\n--- INYECTANDO ANCLAS ---');
        
        let injected = 0;
        const updateStmt = await db.prepare(`
            UPDATE photos
            SET latitude = ?, longitude = ?,
                location_name = ?, city = ?, country = ?,
                date_source = 'HEURISTICA_FILENAME'
            WHERE id = ?
        `);
        
        for (const photo of blindPhotos) {
            const location = extractLocationFromFilename(photo.filename);
            if (location) {
                await updateStmt.run(
                    roundCoord(location.lat),
                    roundCoord(location.lng),
                    location.name,
                    location.name.split(',')[0] || '',
                    location.name.split(',')[1] || '',
                    photo.id
                );
                injected++;
            }
        }
        
        console.log(`Anclas inyectadas: ${injected}\n`);
        
        // 5. Heritage propagation
        console.log('--- HERITAGE PROPAGATION ---');
        
        const anchors = await db.all(`
            SELECT id, date_taken, latitude, longitude, location_name, city, country, file_path
            FROM photos
            WHERE date_source = 'HEURISTICA_FILENAME'
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
            ORDER BY date_taken
        `);
        
        let propagated = 0;
        const propagateStmt = await db.prepare(`
            UPDATE photos
            SET latitude = ?, longitude = ?,
                location_name = ?, city = ?, country = ?,
                date_source = 'HERITAGE_FROM_FILENAME'
            WHERE id = ?
        `);
        
        for (const photo of blindPhotos) {
            if (extractLocationFromFilename(photo.filename)) continue; // Skip already anchored
            
            const photoTs = new Date(photo.date_taken).getTime();
            const photoFolder = photo.file_path.replace(/\\/g, '/').substring(0, photo.file_path.replace(/\\/g, '/').lastIndexOf('/'));
            
            let bestAnchor = null;
            let bestDiff = Infinity;
            
            for (const anchor of anchors) {
                const anchorTs = new Date(anchor.date_taken).getTime();
                const diff = Math.abs(photoTs - anchorTs);
                const anchorFolder = anchor.file_path.replace(/\\/g, '/').substring(0, anchor.file_path.replace(/\\/g, '/').lastIndexOf('/'));
                
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
        
        console.log(`Fotos propagadas: ${propagated}\n`);
        
        // 6. Final stats
        const stats = await db.get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND abs(latitude) > 0.001 THEN 1 ELSE 0 END) as with_gps,
                SUM(CASE WHEN date_source = 'HEURISTICA_FILENAME' THEN 1 ELSE 0 END) as heuristica_filename,
                SUM(CASE WHEN date_source = 'HERITAGE_FROM_FILENAME' THEN 1 ELSE 0 END) as heritage_filename
            FROM photos
        `);
        
        console.log('=== REPORTE FINAL ===');
        console.log(`Total fotos: ${stats.total}`);
        console.log(`Con GPS: ${stats.with_gps} (${((stats.with_gps/stats.total)*100).toFixed(1)}%)`);
        console.log(`HEURISTICA_FILENAME: ${stats.heuristica_filename}`);
        console.log(`HERITAGE_FROM_FILENAME: ${stats.heritage_filename}`);
        console.log(`Total enriquecidas: ${(stats.heuristica_filename||0) + (stats.heritage_filename||0)}`);
        
        console.log('\n✅ AUDITORÍA COMPLETADA');
        
    } catch (error) {
        console.error('❌ ERROR:', error.message);
    } finally {
        await db.close();
    }
}

filenameExtractionAudit();
