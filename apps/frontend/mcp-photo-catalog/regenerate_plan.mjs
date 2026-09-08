/**
 * Regenera el plan de reorganización usando nombres REALES de archivo
 * Estructura destino: Viajes/{TripFolder}/{YYYY-MM}/{filename}
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const REORG_PLAN = './reorganization_plan.csv';
const REORG_JSON = './reorganization_plan.json';
const BASE_TARGET = 'F:\\Fotos_Organizadas';

const TRIP_MAP = {
  'argentina-2011': 'Argentina_2011',
  'argentina-2025': 'Argentina_2025',
  'slovenia-2015': 'Eslovenia_2015',
  'italy-2023': 'Italia_2023',
  'crete-2013': 'Creta_2013',
  'croatia-montenegro-2010': 'Croacia_Montenegro_2010',
  'bosnia-2023': 'Bosnia_2023',
  'denmark-2024': 'Dinamarca_2024',
  'cyprus': 'Chipre',
};

function extractYearMonth(dateTaken) {
  if (!dateTaken) return 'Unknown-Unknown';
  const match = dateTaken.match(/^(\d{4})-(\d{2})/);
  return match ? `${match[1]}-${match[2]}` : 'Unknown-Unknown';
}

function getTargetPath(photo, tripFolder) {
  const yearMonth = extractYearMonth(photo.date_taken);
  const filename = photo.filename;
  return path.join(BASE_TARGET, 'Viajes', tripFolder, yearMonth, filename);
}

function getLocalPath(photo) {
  const year = photo.date_taken ? photo.date_taken.substring(0, 4) : 'Unknown';
  return path.join(BASE_TARGET, 'Sin_Viaje', year, photo.filename);
}

const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');

const photos = db.prepare(`
  SELECT id, file_path, filename, trip_name, date_taken
  FROM photos
  WHERE file_path IS NOT NULL
`).all();

console.log(`📸 Total fotos: ${photos.length.toLocaleString()}`);

// Generate plan
const plan = [];
const pathCount = new Map();
let conflicts = 0;

for (const photo of photos) {
  let tripName = photo.trip_name || 'Sin_Viaje';
  let tripFolder = TRIP_MAP[tripName] || tripName;
  
  let targetPath = tripName !== 'Sin_Viaje' 
    ? getTargetPath(photo, tripFolder)
    : getLocalPath(photo);
  
  // Handle collisions
  const count = pathCount.get(targetPath) || 0;
  if (count > 0) {
    const ext = path.extname(targetPath);
    const base = path.basename(targetPath, ext);
    const dir = path.dirname(targetPath);
    targetPath = path.join(dir, `${base}_${count}${ext}`);
    conflicts++;
  }
  pathCount.set(targetPath, count + 1);
  
  plan.push({
    id: photo.id,
    src: photo.file_path,
    dst: targetPath,
    trip: tripName,
  });
}

// Write CSV
const csv = 'id,src,dst,trip\n' + plan.map(p => 
  `${p.id},"${p.src.replace(/"/g, '""')}","${p.dst.replace(/"/g, '""')}",${p.trip}`
).join('\n');
fs.writeFileSync(REORG_PLAN, csv);
console.log(`✅ CSV: ${REORG_PLAN}`);

// Write JSON summary
const byTrip = {};
for (const p of plan) {
  const folder = TRIP_MAP[p.trip] || p.trip;
  if (!byTrip[folder]) byTrip[folder] = { count: 0, display: folder };
  byTrip[folder].count++;
}

fs.writeFileSync(REORG_JSON, JSON.stringify({ 
  total: plan.length, 
  conflicts, 
  byTrip,
  tripMap: TRIP_MAP 
}, null, 2));
console.log(`✅ JSON: ${REORG_JSON}`);

// Summary
console.log('\n=== RESUMEN ===');
const sorted = Object.entries(byTrip).sort((a, b) => b[1].count - a[1].count);
for (const [folder, data] of sorted) {
  console.log(`  ${folder}: ${data.count.toLocaleString()}`);
}
console.log(`\n  Total: ${plan.length.toLocaleString()} | Conflictos: ${conflicts}`);

db.close();
