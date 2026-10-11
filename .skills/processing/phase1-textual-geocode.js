// phase1-textual-geocode.js - Fase 1: Geocodificación textual de carpetas
// Ejecutar con: node phase1-textual-geocode.js

import { readFileSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Diccionario de coordenadas conocidas (Israel + Argentina + Europa)
const KNOWN_LOCATIONS = {
    // === ISRAEL ===
    'תל אביב': { lat: 32.0853, lng: 34.7818, name: 'Tel Aviv' },
    'ירושלים': { lat: 31.7683, lng: 35.2137, name: 'Jerusalem' },
    'חיפה': { lat: 32.7940, lng: 34.9896, name: 'Haifa' },
    'באר שבע': { lat: 31.2530, lng: 34.7915, name: 'Beer Sheva' },
    'אילת': { lat: 29.5577, lng: 34.9519, name: 'Eilat' },
    'חדרה': { lat: 32.4340, lng: 34.9196, name: 'Hadera' },
    'נתניה': { lat: 32.3286, lng: 34.8590, name: 'Netanya' },
    'אשדוד': { lat: 31.8040, lng: 34.6553, name: 'Ashdod' },
    'אשקלון': { lat: 31.6688, lng: 34.5743, name: 'Ashkelon' },
    'כרמיאל': { lat: 32.9122, lng: 35.2922, name: 'Karmiel' },
    'צפת': { lat: 32.9646, lng: 35.4937, name: 'Safed' },
    'טבריה': { lat: 32.7922, lng: 35.5312, name: 'Tiberias' },
    'עכו': { lat: 32.9278, lng: 35.0831, name: 'Acre' },
    'נהריה': { lat: 33.0062, lng: 35.0953, name: 'Nahariya' },
    'כרתים': { lat: 35.2401, lng: 24.4691, name: 'Crete, Greece' },
    'רודוס': { lat: 36.4341, lng: 28.2176, name: 'Rhodes, Greece' },
    
    // === ARGENTINA ===
    'בואנוס איירס': { lat: -34.6037, lng: -58.3816, name: 'Buenos Aires' },
    'בואנוס': { lat: -34.6037, lng: -58.3816, name: 'Buenos Aires' },
    'סנטה פה': { lat: -31.6488, lng: -60.6985, name: 'Santa Fe' },
    'קורIENTס': { lat: -27.4699, lng: -58.8306, name: 'Corrientes' },
    'פוזס': { lat: -27.3671, lng: -55.8961, name: 'Posadas' },
    'סאלטה': { lat: -24.7829, lng: -65.4234, name: 'Salta' },
    '샌 קרלוס דה בא_rluche': { lat: -41.1335, lng: -71.3103, name: 'Bariloche' },
    'בא_rluche': { lat: -41.1335, lng: -71.3103, name: 'Bariloche' },
    'קלפטה': { lat: -46.5432, lng: -71.6318, name: 'Calafate, Argentina' },
    'טרמולין': { lat: -43.0449, lng: -71.3983, name: 'Trevelin, Argentina' },
    'טרוולין': { lat: -43.0449, lng: -71.3983, name: 'Trevelin, Argentina' },
    'לוס אנטיגואוס': { lat: -46.5432, lng: -71.6318, name: 'Los Antiguos, Argentina' },
    'מוא罗斯': { lat: -35.0519, lng: -57.5194, name: 'Morón, Buenos Aires' },
    'טורס': { lat: -38.8262, lng: -68.0611, name: 'Neuquén, Argentina' },
    'מאנדוזה': { lat: -32.8895, lng: -68.8458, name: 'Mendoza, Argentina' },
    'מאנדוסה': { lat: -32.8895, lng: -68.8458, name: 'Mendoza, Argentina' },
    'מנדוסה': { lat: -32.8895, lng: -68.8458, name: 'Mendoza, Argentina' },
    'טרלאו': { lat: -43.2489, lng: -71.3375, name: 'Trelew, Argentina' },
    'אושואיה': { lat: -54.8019, lng: -68.3030, name: 'Ushuaia, Argentina' },
    'לה פלאטה': { lat: -34.9214, lng: -57.9544, name: 'La Plata, Argentina' },
    'רוסריו': { lat: -32.9468, lng: -60.6393, name: 'Rosario, Argentina' },
    'טיגרה': { lat: -34.4267, lng: -58.5796, name: 'Tigre, Argentina' },
    'פונטה דל אינקה': { lat: -32.8281, lng: -69.8113, name: 'Puente del Inca, Argentina' },
    'קרטארו': { lat: -20.5888, lng: -100.3899, name: 'Querétaro, Mexico' },
    
    // === MONTENEGRO ===
    'דוברובניק': { lat: 42.6507, lng: 18.0944, name: 'Dubrovnik, Croatia' },
    'בודווה': { lat: 42.2895, lng: 18.8394, name: 'Budva, Montenegro' },
    'קולשין': { lat: 42.8254, lng: 19.5188, name: 'Kolašin, Montenegro' },
    'קולאשין': { lat: 42.8254, lng: 19.5188, name: 'Kolašin, Montenegro' },
    'הדורמיטור': { lat: 43.1500, lng: 19.0333, name: 'Durmitor, Montenegro' },
    'מפרץ קוטור': { lat: 42.4247, lng: 18.7712, name: 'Bay of Kotor, Montenegro' },
    'הר לובצן': { lat: 42.3992, lng: 18.7806, name: 'Mount Lovćen, Montenegro' },
    'אגם סקאדאר': { lat: 42.1000, lng: 19.1000, name: 'Lake Skadar, Montenegro' },
    'ניקשיץ': { lat: 42.7777, lng: 18.9536, name: 'Nikšić, Montenegro' },
    'מונטנגרו': { lat: 42.7087, lng: 19.3744, name: 'Montenegro' },
    
    // === SLOVENIA ===
    'סלובניה': { lat: 46.1512, lng: 14.9955, name: 'Slovenia' },
    'בלד': { lat: 46.3683, lng: 14.1136, name: 'Bled, Slovenia' },
    'ליובליאנה': { lat: 46.0569, lng: 14.5058, name: 'Ljubljana, Slovenia' },
    'פוסטויינה': { lat: 45.7790, lng: 14.2094, name: 'Postojna, Slovenia' },
    'PLITוויצה': { lat: 44.8654, lng: 15.5820, name: 'Plitvice, Croatia' },
    
    // === CROATIA ===
    'קרואטיה': { lat: 45.1000, lng: 15.2000, name: 'Croatia' },
    'זאגרב': { lat: 45.8150, lng: 15.9819, name: 'Zagreb, Croatia' },
    'ספליט': { lat: 43.5081, lng: 16.4402, name: 'Split, Croatia' },
    
    // === ITALY ===
    'איטליה': { lat: 41.8719, lng: 12.5674, name: 'Italy' },
    'רומא': { lat: 41.9028, lng: 12.4964, name: 'Rome, Italy' },
    'ונציה': { lat: 45.4408, lng: 12.3155, name: 'Venice, Italy' },
    'מילאנו': { lat: 45.4642, lng: 9.1900, name: 'Milan, Italy' },
    'פירנצה': { lat: 43.7696, lng: 11.2558, name: 'Florence, Italy' },
    'פיזה': { lat: 43.7228, lng: 10.4017, name: 'Pisa, Italy' },
    'ותיקן': { lat: 41.9029, lng: 12.4534, name: 'Vatican City' },
    
    // === CYPRUS ===
    'קפריסין': { lat: 35.1264, lng: 33.4299, name: 'Cyprus' },
    
    // === BOSNIA ===
    'בוסניה': { lat: 43.9159, lng: 17.6791, name: 'Bosnia and Herzegovina' },
    'סרייבו': { lat: 43.8563, lng: 18.4131, name: 'Sarajevo, Bosnia' },
    
    // === GREECE ===
    'יוון': { lat: 39.0742, lng: 21.8243, name: 'Greece' },
    'אתונה': { lat: 37.9838, lng: 23.7275, name: 'Athens, Greece' },
    'סנטוריני': { lat: 36.3932, lng: 25.4615, name: 'Santorini, Greece' },
    
    // === JORDAN ===
    'ירדן': { lat: 30.5852, lng: 36.2384, name: 'Jordan' },
    'עמאן': { lat: 31.9454, lng: 35.9284, name: 'Amman, Jordan' },
    'פטרה': { lat: 30.3285, lng: 35.4444, name: 'Petra, Jordan' },
    
    // === SPAIN ===
    'ברצלונה': { lat: 41.3851, lng: 2.1734, name: 'Barcelona, Spain' },
    'מדריד': { lat: 40.4168, lng: -3.7038, name: 'Madrid, Spain' },
    
    // === PORTUGAL ===
    'ליסבון': { lat: 38.7223, lng: -9.1393, name: 'Lisbon, Portugal' },
    
    // === CZECH ===
    'פראג': { lat: 50.0755, lng: 14.4378, name: 'Prague, Czech Republic' },
    
    // === HUNGARY ===
    'בודפשט': { lat: 47.4979, lng: 19.0402, name: 'Budapest, Hungary' },
    
    // === THAILAND ===
    'בנגקוק': { lat: 13.7563, lng: 100.5018, name: 'Bangkok, Thailand' },
    'פוקט': { lat: 7.8804, lng: 98.3923, name: 'Phuket, Thailand' },
    
    // === ISRAEL SPECIFIC ===
    'הר כרכום': { lat: 30.8589, lng: 34.7833, name: 'Har Karkom, Israel' },
    'בקעת תמנע': { lat: 29.8500, lng: 34.9833, name: 'Timna Valley, Israel' },
    'נווה יטבתה': { lat: 29.8833, lng: 35.0667, name: 'Nevatot, Israel' },
    'נחל דרוך': { lat: 31.4167, lng: 34.3667, name: 'Nachal Dror, Israel' },
    'הר אמיר': { lat: 31.4167, lng: 34.3667, name: 'Har Amir, Israel' },
    'חוף אשדוד': { lat: 31.7833, lng: 34.6333, name: 'Ashdod Beach, Israel' },
    'באר אורה': { lat: 29.9000, lng: 35.0333, name: "Be'er Ora, Israel" },
    'גליל התחתון': { lat: 32.7500, lng: 35.4167, name: 'Lower Galilee, Israel' },
    
    // === COMMON FOLDER NAMES ===
    'My Scans': { lat: null, lng: null, name: 'Scans (unknown location)' },
    'Camera Uploads': { lat: null, lng: null, name: 'Camera Uploads (unknown)' },
    'Tablet': { lat: null, lng: null, name: 'Tablet (unknown)' },
    'colash': { lat: null, lng: null, name: 'Collage (unknown)' },
    'Downloaded Albums': { lat: null, lng: null, name: 'Downloaded (unknown)' },
    'Roblox': { lat: null, lng: null, name: 'Game screenshot (unknown)' },
    'heladera': { lat: null, lng: null, name: 'Fridge photo (unknown)' },
    'Work': { lat: null, lng: null, name: 'Work (unknown)' },
};

// Detectar nombre de lugar en ruta
function detectLocationFromPath(folderPath) {
    const normalized = folderPath
        .replace(/\\/g, '/')
        .replace(/F:\//g, '')
        .replace(/F:/g, '');
    
    // Buscar coincidencias en orden de especificidad (más específico primero)
    const sortedKeys = Object.keys(KNOWN_LOCATIONS).sort((a, b) => b.length - a.length);
    
    for (const key of sortedKeys) {
        if (normalized.includes(key)) {
            return {
                key,
                ...KNOWN_LOCATIONS[key]
            };
        }
    }
    
    return null;
}

async function phase1TextualGeocode() {
    console.log('=== FASE 1: GEOCODIFICACIÓN TEXTUAL ===\n');
    
    // Leer folder-anchors.json
    const jsonPath = join(__dirname, 'api', 'folder-anchors.json');
    const folderData = JSON.parse(readFileSync(jsonPath, 'utf8'));
    
    const totalFolders = Object.keys(folderData).length;
    console.log(`Total carpetas: ${totalFolders}\n`);
    
    let geocoded = 0;
    let skipped = 0;
    let generic = 0;
    
    const results = {
        geocoded: [],
        generic: [],
        skipped: []
    };
    
    for (const [folder, data] of Object.entries(folderData)) {
        const location = detectLocationFromPath(folder);
        
        if (location && location.lat !== null) {
            // Geocoded successfully
            folderData[folder].lat = location.lat;
            folderData[folder].lng = location.lng;
            folderData[folder].location_name = location.name;
            geocoded++;
            results.geocoded.push({ folder, name: location.name, count: data.count });
        } else if (location && location.lat === null) {
            // Generic folder - needs vision
            generic++;
            results.generic.push({ folder, name: location.name, count: data.count });
        } else {
            skipped++;
            results.skipped.push({ folder, count: data.count });
        }
    }
    
    // Save updated JSON
    writeFileSync(jsonPath, JSON.stringify(folderData, null, 2));
    
    console.log('=== RESULTADOS ===');
    console.log(`Geocoded: ${geocoded} carpetas`);
    console.log(`Generic (need vision): ${generic} carpetas`);
    console.log(`Skipped (unknown): ${skipped} carpetas\n`);
    
    if (results.geocoded.length > 0) {
        console.log('--- CARPETAS GEOCODIFICADAS ---');
        for (const r of results.geocoded.slice(0, 30)) {
            console.log(`  ${r.name}: ${r.count} fotos`);
        }
        if (results.geocoded.length > 30) {
            console.log(`  ... y ${results.geocoded.length - 30} más`);
        }
    }
    
    if (results.generic.length > 0) {
        console.log('\n--- CARPETAS GENÉRICAS (requieren visión) ---');
        for (const r of results.generic) {
            console.log(`  ${r.folder}: ${r.count} fotos`);
        }
    }
    
    // Save generic list for Phase 2
    writeFileSync(
        join(__dirname, 'generic-folders.json'),
        JSON.stringify(results.generic, null, 2)
    );
    
    console.log('\n✅ FASE 1 COMPLETADA');
    console.log(`Guardado: api/folder-anchors.json (${geocoded} geocoded)`);
    console.log(`Guardado: generic-folders.json (${generic} para visión)`);
}

phase1TextualGeocode();
