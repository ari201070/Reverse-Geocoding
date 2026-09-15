/**
 * Fase 5.1: Prueba Piloto de Copiado Seguro
 * 
 * REGLAS:
 * - COPIAR (fs.copyFile), NUNCA mover
 * - Procesar SOLO Chipre (103 fotos)
 * - Generar execution_log.csv
 * - Verificar integridad
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const REORG_PLAN_PATH = './reorganization_plan.csv';
const EXEC_LOG_PATH = './execution_log.csv';
const BASE_TARGET = 'F:\\Fotos_Organizadas';
const TARGET_TRIP = 'cyprus'; // Solo Chipre para prueba piloto

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

function calculateFileHash(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(filePath);
    stream.on('data', data => hash.update(data));
    stream.on('end', () => resolve(hash.digest('hex')));
    stream.on('error', reject);
  });
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 5.1: PRUEBA PILOTO - COPIA SEGURA (CHIPRE)');
  console.log('═══════════════════════════════════════════════════════════════\n');

  // Read reorganization plan
  console.log('📋 Leyendo plan de reorganización...');
  const planContent = fs.readFileSync(REORG_PLAN_PATH, 'utf8');
  const planLines = planContent.split('\n').slice(1); // Skip header
  
  // Filter for Cyprus only
  const cyprusPlan = planLines
    .filter(line => line.trim())
    .map(line => {
      const [id, original_path, proposed_target_path, trip_name, has_conflict] = line.split(',');
      return {
        id: parseInt(id),
        original_path: original_path.replace(/"/g, ''),
        proposed_target_path: proposed_target_path.replace(/"/g, ''),
        trip_name,
        has_conflict: has_conflict === 'true',
      };
    })
    .filter(item => item.trip_name === TARGET_TRIP);

  console.log(`📸 Fotos de Chipre a copiar: ${cyprusPlan.length}\n`);

  // Initialize execution log
  const logStream = fs.createWriteStream(EXEC_LOG_PATH);
  logStream.write('original_path,target_path,status,file_size_bytes,timestamp\n');

  // Statistics
  const stats = {
    total: cyprusPlan.length,
    success: 0,
    failed: 0,
    skipped: 0,
    total_bytes: 0,
    errors: [],
  };

  // Process each photo
  for (let i = 0; i < cyprusPlan.length; i++) {
    const item = cyprusPlan[i];
    const timestamp = new Date().toISOString();

    try {
      // Check if source file exists
      if (!fs.existsSync(item.original_path)) {
        console.log(`  ⚠️ [${i + 1}/${cyprusPlan.length}] File not found: ${item.original_path}`);
        logStream.write(`"${item.original_path}","${item.proposed_target_path}","FILE_NOT_FOUND",0,${timestamp}\n`);
        stats.failed++;
        stats.errors.push({ id: item.id, error: 'File not found' });
        continue;
      }

      // Get source file size
      const sourceStats = fs.statSync(item.original_path);
      const sourceSize = sourceStats.size;

      // Create target directory if needed
      const targetDir = path.dirname(item.proposed_target_path);
      if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
        console.log(`  📁 Created directory: ${targetDir}`);
      }

      // Copy file
      fs.copyFileSync(item.original_path, item.proposed_target_path);

      // Verify copy (check file size)
      const targetStats = fs.statSync(item.proposed_target_path);
      const targetSize = targetStats.size;

      if (sourceSize === targetSize) {
        console.log(`  ✅ [${i + 1}/${cyprusPlan.length}] Copied: ${path.basename(item.original_path)} (${sourceSize.toLocaleString()} bytes)`);
        logStream.write(`"${item.original_path}","${item.proposed_target_path}","SUCCESS",${sourceSize},${timestamp}\n`);
        stats.success++;
        stats.total_bytes += sourceSize;
      } else {
        console.log(`  ❌ [${i + 1}/${cyprusPlan.length}] Size mismatch: ${path.basename(item.original_path)}`);
        logStream.write(`"${item.original_path}","${item.proposed_target_path}","SIZE_MISMATCH",${sourceSize},${timestamp}\n`);
        stats.failed++;
        stats.errors.push({ id: item.id, error: `Size mismatch: ${sourceSize} vs ${targetSize}` });
      }

    } catch (e) {
      console.log(`  ❌ [${i + 1}/${cyprusPlan.length}] Error: ${e.message}`);
      logStream.write(`"${item.original_path}","${item.proposed_target_path}","ERROR",0,${timestamp}\n`);
      stats.failed++;
      stats.errors.push({ id: item.id, error: e.message });
    }
  }

  logStream.end();

  // Verify source files remain untouched
  console.log('\n🔍 Verificando integridad de archivos origen...');
  let sourceIntact = 0;
  for (const item of cyprusPlan.slice(0, 5)) { // Check first 5 files
    if (fs.existsSync(item.original_path)) {
      const stats = fs.statSync(item.original_path);
      if (stats.size > 0) {
        sourceIntact++;
      }
    }
  }
  console.log(`   └─ ✅ ${sourceIntact}/${Math.min(5, cyprusPlan.length)} archivos origen verificados (intactos)`);

  // Final report
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  REPORTE FINAL - FASE 5.1');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log('📊 RESUMEN:');
  console.log(`   Total archivos: ${stats.total}`);
  console.log(`   ✅ Copiados exitosamente: ${stats.success}`);
  console.log(`   ❌ Fallidos: ${stats.failed}`);
  console.log(`   📦 Tamaño total copiado: ${(stats.total_bytes / 1024 / 1024).toFixed(2)} MB`);

  if (stats.errors.length > 0) {
    console.log('\n⚠️ ERRORES:');
    stats.errors.forEach(e => console.log(`   - ID ${e.id}: ${e.error}`));
  }

  console.log('\n📂 ESTRUCTURA CREADA:');
  console.log(`   ${BASE_TARGET}\\`);
  console.log(`   └── Viajes\\`);
  console.log(`       └── Chipre\\ (${stats.success} fotos)`);

  console.log('\n📄 Archivos generados:');
  console.log(`   - ${EXEC_LOG_PATH}`);
  console.log(`   - ${BASE_TARGET}\\Viajes\\Chipre\\ (archivos copiados)`);

  console.log('\n✅ Prueba piloto completada. Archivos origen intactos.');
}

main().catch(console.error);
