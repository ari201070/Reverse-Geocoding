/**
 * Fase 4: Simulación de Reorganización (Dry-Run)
 * 
 * REGLAS:
 * - NO mover archivos reales
 * - Generar rutas destino basadas en trip_name
 * - Detectar y resolver colisiones de nombres
 * - Exportar CSV y JSON
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const CSV_PATH = './reorganization_plan.csv';
const JSON_PATH = './reorganization_plan.json';
const BASE_TARGET = 'F:\\Fotos_Organizadas';

// Trip name mapping for folder names
const TRIP_FOLDER_MAP = {
  'argentina-2011': 'Argentina_2011',
  'argentina-2025': 'Argentina_2025',
  'slovenia-2015': 'Eslovenia_2015',
  'italy-2023': 'Italia_2023',
  'crete-2013': 'Creta_2013',
  'croatia-montenegro-2010': 'Croacia_Montenegro_2010',
  'bosnia-2023': 'Bosnia_2023',
  'denmark-2024': 'Dinamarca_2024',
  'denmark-2020': 'Dinamarca_2020',
  'cyprus': 'Chipre',
};

function extractDateInfo(dateStr) {
  if (!dateStr) return { year: 'Unknown', month: 'Unknown' };
  const parts = dateStr.split(' ')[0].split('-');
  return {
    year: parts[0] || 'Unknown',
    month: parts[1] || '00',
  };
}

function getTargetPath(photo, tripFolder) {
  const dateInfo = extractDateInfo(photo.date_taken);
  const ext = path.extname(photo.filename);
  const name = path.basename(photo.filename, ext);
  
  return path.join(
    BASE_TARGET,
    'Viajes',
    tripFolder,
    `${dateInfo.year}-${dateInfo.month}`,
    `${name}${ext}`
  );
}

function getLocalTargetPath(photo) {
  const dateInfo = extractDateInfo(photo.date_taken);
  const ext = path.extname(photo.filename);
  const name = path.basename(photo.filename, ext);
  
  return path.join(
    BASE_TARGET,
    'Sin_Viaje',
    dateInfo.year,
    `${name}${ext}`
  );
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 4: SIMULACIÓN DE REORGANIZACIÓN (DRY-RUN)');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');

  // Get all photos
  const photos = db.prepare(`
    SELECT id, file_path, filename, trip_name, country, date_taken
    FROM photos
    WHERE file_path IS NOT NULL
  `).all();

  console.log(`📸 Total fotos a procesar: ${photos.length.toLocaleString()}\n`);

  // Track target paths for collision detection
  const targetPathCount = new Map();
  const plan = [];
  let conflictCount = 0;

  for (const photo of photos) {
    let targetPath;
    let tripName = photo.trip_name || 'Sin_Viaje';
    let hasConflict = false;

    if (photo.trip_name && TRIP_FOLDER_MAP[photo.trip_name]) {
      // Photo with trip
      const tripFolder = TRIP_FOLDER_MAP[photo.trip_name];
      targetPath = getTargetPath(photo, tripFolder);
    } else {
      // Local photo (Israel or no trip)
      targetPath = getLocalTargetPath(photo);
    }

    // Check for collision
    const currentCount = targetPathCount.get(targetPath) || 0;
    if (currentCount > 0) {
      // Add suffix to resolve conflict
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

  // Generate CSV
  console.log('📄 Generando CSV...');
  const csvHeader = 'id,original_path,proposed_target_path,trip_name,has_conflict\n';
  const csvRows = plan.map(p => 
    `${p.id},"${p.original_path.replace(/"/g, '""')}","${p.proposed_target_path.replace(/"/g, '""')}",${p.trip_name},${p.has_conflict}`
  ).join('\n');
  fs.writeFileSync(CSV_PATH, csvHeader + csvRows);
  console.log(`   └─ ✅ CSV guardado en: ${CSV_PATH}`);

  // Generate JSON summary
  console.log('📄 Generando JSON...');
  
  // Group by trip
  const byTrip = {};
  for (const item of plan) {
    const trip = item.trip_name;
    if (!byTrip[trip]) {
      byTrip[trip] = { count: 0, conflicts: 0, sample_paths: [] };
    }
    byTrip[trip].count++;
    if (item.has_conflict) byTrip[trip].conflicts++;
    if (byTrip[trip].sample_paths.length < 3) {
      byTrip[trip].sample_paths.push(item.proposed_target_path);
    }
  }

  const jsonSummary = {
    total_photos: plan.length,
    total_conflicts: conflictCount,
    by_trip: byTrip,
    generated_at: new Date().toISOString(),
  };

  fs.writeFileSync(JSON_PATH, JSON.stringify(jsonSummary, null, 2));
  console.log(`   └─ ✅ JSON guardado en: ${JSON_PATH}`);

  // Console report
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  REPORTE DE SIMULACIÓN');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log('📊 RESUMEN:');
  console.log(`   Total archivos en plan: ${plan.length.toLocaleString()}`);
  console.log(`   Colisiones detectadas: ${conflictCount.toLocaleString()}`);
  console.log(`   Archivos únicos de destino: ${targetPathCount.size.toLocaleString()}\n`);

  console.log('🔹 DESGLOSE POR VIAJE:');
  const tripEntries = Object.entries(byTrip).sort((a, b) => b[1].count - a[1].count);
  for (const [trip, data] of tripEntries) {
    console.log(`   ${trip}: ${data.count.toLocaleString()} fotos (${data.conflicts} conflictos)`);
  }

  console.log('\n📂 ESTRUCTURA PROPUESTA:');
  console.log(`   ${BASE_TARGET}\\`);
  console.log(`   ├── Viajes\\`);
  for (const [trip, folder] of Object.entries(TRIP_FOLDER_MAP)) {
    const count = byTrip[trip]?.count || 0;
    if (count > 0) {
      console.log(`   │   ├── ${folder}\\ (${count.toLocaleString()} fotos)`);
    }
  }
  console.log(`   └── Sin_Viaje\\`);
  console.log(`       └── [Año]\\ (${(byTrip['Sin_Viaje']?.count || 0).toLocaleString()} fotos)`);

  console.log('\n✅ Simulación completada. No se movieron archivos reales.');

  db.close();
}

main().catch(console.error);
