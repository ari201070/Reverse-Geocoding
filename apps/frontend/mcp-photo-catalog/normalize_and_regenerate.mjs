/**
 * Normalización Completa y Regeneración del Plan
 * 
 * REGLAS:
 * - Trip names en español puro (sin hebreo)
 * - Formato YYYY-MM para subcarpetas
 * - Caracteres limpios (sin acentos, espacios → guiones bajos)
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const REORG_PLAN_PATH = './reorganization_plan.csv';
const REORG_JSON_PATH = './reorganization_plan.json';
const BASE_TARGET = 'F:\\Fotos_Organizadas';

// Trip name mapping: database value → normalized Spanish name
const TRIP_NORMALIZATION = {
  'argentina-2011': { folder: 'Argentina_2011', display: 'Argentina 2011' },
  'argentina-2025': { folder: 'Argentina_2025', display: 'Argentina 2025' },
  'slovenia-2015': { folder: 'Eslovenia_2015', display: 'Eslovenia 2015' },
  'italy-2023': { folder: 'Italia_2023', display: 'Italia 2023' },
  'crete-2013': { folder: 'Creta_2013', display: 'Creta 2013' },
  'croatia-montenegro-2010': { folder: 'Croacia_Montenegro_2010', display: 'Croacia+Montenegro 2010' },
  'bosnia-2023': { folder: 'Bosnia_2023', display: 'Bosnia 2023' },
  'denmark-2024': { folder: 'Dinamarca_2024', display: 'Dinamarca 2024' },
  'denmark-2020': { folder: 'Dinamarca_2020', display: 'Dinamarca 2020' },
  'cyprus': { folder: 'Chipre', display: 'Chipre' },
};

// Hebrew to Spanish translations
const HEBREW_TRANSLATIONS = {
  'טיול לארגentina': 'Viaje_Argentina',
  'ארגנטינה': 'Argentina',
  'פיזה': 'Pisa',
  'רומא': 'Roma',
  'ונציה': 'Venecia',
  'פירנצה': 'Florencia',
  'מילאנו': 'Milano',
  'נאפולי': 'Napoles',
  'איטליה': 'Italia',
  'סלובניה': 'Eslovenia',
  'קרואטיה': 'Croacia',
  'מונטנגרו': 'Montenegro',
  'בוסניה': 'Bosnia',
  'יוון': 'Grecia',
  'כרתים': 'Creta',
  'קופנהגן': 'Copenhagen',
  'דנמרק': 'Dinamarca',
  'קפריסין': 'Chipre',
  'לאגו פואלו': 'Lago_Puelo',
  'ברילוצ\'ה': 'Bariloche',
  'מנדוזה': 'Mendoza',
  'בואנוס איירס': 'Buenos_Aires',
  'סאלטה': 'Salta',
  'חוחוי': 'Jujuy',
  'קורדובה': 'Cordoba',
};

function normalizeFileName(name) {
  if (!name) return name;
  
  // Remove Hebrew text
  let normalized = name.replace(/[\u0590-\u05FF]+/g, '');
  
  // Remove parentheses
  normalized = normalized.replace(/[()]/g, '');
  
  // Replace spaces with underscores
  normalized = normalized.replace(/\s+/g, '_');
  
  // Remove special characters except underscore, hyphen, dot
  normalized = normalized.replace(/[^a-zA-Z0-9._-]/g, '');
  
  // Remove leading/trailing underscores
  normalized = normalized.replace(/^_+|_+$/g, '');
  
  return normalized || 'unknown';
}

function extractYearMonth(dateStr) {
  if (!dateStr) return 'Unknown-Unknown';
  const match = dateStr.match(/^(\d{4})-(\d{2})/);
  if (match) {
    return `${match[1]}-${match[2]}`;
  }
  return 'Unknown-Unknown';
}

function getTargetPath(photo, tripFolder) {
  const yearMonth = extractYearMonth(photo.date_taken);
  const ext = path.extname(photo.filename);
  const cleanName = normalizeFileName(path.basename(photo.filename, ext));
  
  return path.join(
    BASE_TARGET,
    'Viajes',
    tripFolder,
    yearMonth,
    `${cleanName}${ext}`
  );
}

function getLocalTargetPath(photo) {
  const year = photo.date_taken ? photo.date_taken.substring(0, 4) : 'Unknown';
  const ext = path.extname(photo.filename);
  const cleanName = normalizeFileName(path.basename(photo.filename, ext));
  
  return path.join(
    BASE_TARGET,
    'Sin_Viaje',
    year,
    `${cleanName}${ext}`
  );
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  NORMALIZACIÓN Y REGENERACIÓN DEL PLAN');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');

  // 1. Show normalization table
  console.log('📋 TABLA DE NORMALIZACIÓN:');
  console.log('─'.repeat(60));
  console.log('Original (DB)'.padEnd(35) + '→ Normalizado (Español)');
  console.log('─'.repeat(60));
  
  for (const [dbValue, info] of Object.entries(TRIP_NORMALIZATION)) {
    console.log(dbValue.padEnd(35) + '→ ' + info.display);
  }
  console.log('─'.repeat(60));
  console.log('');

  // 2. Get all photos
  const photos = db.prepare(`
    SELECT id, file_path, filename, trip_name, country, date_taken
    FROM photos
    WHERE file_path IS NOT NULL
  `).all();

  console.log(`📸 Total fotos: ${photos.length.toLocaleString()}\n`);

  // 3. Generate reorganization plan
  console.log('📝 Generando plan de reorganización...');
  
  const plan = [];
  const targetPathCount = new Map();
  let conflictCount = 0;

  for (const photo of photos) {
    let targetPath;
    let tripName = photo.trip_name || 'Sin_Viaje';
    let hasConflict = false;

    if (photo.trip_name && TRIP_NORMALIZATION[photo.trip_name]) {
      const tripFolder = TRIP_NORMALIZATION[photo.trip_name].folder;
      targetPath = getTargetPath(photo, tripFolder);
    } else {
      targetPath = getLocalTargetPath(photo);
    }

    // Check for collision
    const currentCount = targetPathCount.get(targetPath) || 0;
    if (currentCount > 0) {
      const ext = path.extname(targetPath);
      const nameWithoutExt = path.basename(targetPath, ext);
      const dir = path.dirname(targetPath);
      targetPath = path.join(dir, `${nameWithoutExt}_${currentCount}${ext}`);
      hasConflict = true;
      conflictCount++;
    }
    targetPathCount.set(targetPath, currentCount + 1);

    plan.push({
      id: photo.id,
      original_path: photo.file_path,
      proposed_target_path: targetPath,
      trip_name: tripName,
      has_conflict: hasConflict,
    });
  }

  // 4. Generate CSV
  console.log('📄 Generando CSV...');
  const csvHeader = 'id,original_path,proposed_target_path,trip_name,has_conflict\n';
  const csvRows = plan.map(p => 
    `${p.id},"${p.original_path.replace(/"/g, '""')}","${p.proposed_target_path.replace(/"/g, '""')}",${p.trip_name},${p.has_conflict}`
  ).join('\n');
  fs.writeFileSync(REORG_PLAN_PATH, csvHeader + csvRows);
  console.log(`   └─ ✅ CSV: ${REORG_PLAN_PATH}`);

  // 5. Generate JSON summary
  console.log('📄 Generando JSON...');
  
  const byTrip = {};
  for (const item of plan) {
    const trip = item.trip_name;
    if (!byTrip[trip]) {
      byTrip[trip] = { 
        count: 0, 
        conflicts: 0, 
        folder: TRIP_NORMALIZATION[trip]?.folder || trip,
        display: TRIP_NORMALIZATION[trip]?.display || trip,
      };
    }
    byTrip[trip].count++;
    if (item.has_conflict) byTrip[trip].conflicts++;
  }

  const jsonSummary = {
    total_photos: plan.length,
    total_conflicts: conflictCount,
    by_trip: byTrip,
    normalization_map: TRIP_NORMALIZATION,
    generated_at: new Date().toISOString(),
  };

  fs.writeFileSync(REORG_JSON_PATH, JSON.stringify(jsonSummary, null, 2));
  console.log(`   └─ ✅ JSON: ${REORG_JSON_PATH}`);

  // 6. Final report
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  RESUMEN');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log('📊 ESTADÍSTICAS:');
  console.log(`   Total archivos: ${plan.length.toLocaleString()}`);
  console.log(`   Colisiones: ${conflictCount.toLocaleString()}`);

  console.log('\n📂 ESTRUCTURA PROPUESTA:');
  console.log(`   ${BASE_TARGET}\\`);
  console.log(`   ├── Viajes\\`);
  
  const tripEntries = Object.entries(byTrip)
    .filter(([trip]) => trip !== 'Sin_Viaje')
    .sort((a, b) => b[1].count - a[1].count);
  
  for (const [trip, data] of tripEntries) {
    console.log(`   │   ├── ${data.folder}\\ (${data.count.toLocaleString()} fotos)`);
  }
  
  const localCount = byTrip['Sin_Viaje']?.count || 0;
  console.log(`   └── Sin_Viaje\\ (${localCount.toLocaleString()} fotos)`);

  console.log('\n✅ Normalización completada. Archivos listos para copia.');

  db.close();
}

main().catch(console.error);
