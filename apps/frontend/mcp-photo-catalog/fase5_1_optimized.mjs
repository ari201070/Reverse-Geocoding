/**
 * Fase 5.1: Copia Optimizada de Chipre
 * 
 * OPTIMIZACIONES:
 * - Carga CSV en memoria una sola vez
 * - Caché de directorios con Set
 * - Procesamiento concurrente (10 workers)
 * - Buffered logging
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const REORG_PLAN_PATH = './reorganization_plan.csv';
const EXEC_LOG_PATH = './execution_log.csv';
const BASE_TARGET = 'F:\\Fotos_Organizadas';
const TARGET_TRIP = 'cyprus';
const CONCURRENCY = 10;
const LOG_FLUSH_SIZE = 50;

// Cache de directorios creados
const createdDirs = new Set();

// Buffer de logs
const logBuffer = [];
let stats = { success: 0, failed: 0, total_bytes: 0, start_time: Date.now() };

async function ensureDir(dirPath) {
  if (createdDirs.has(dirPath)) return;
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  createdDirs.add(dirPath);
}

async function copyFile(item) {
  const timestamp = new Date().toISOString();
  
  try {
    if (!fs.existsSync(item.original_path)) {
      logBuffer.push(`"${item.original_path}","${item.proposed_target_path}","FILE_NOT_FOUND",0,${timestamp}`);
      stats.failed++;
      return;
    }

    const sourceStats = fs.statSync(item.original_path);
    const targetDir = path.dirname(item.proposed_target_path);
    
    await ensureDir(targetDir);
    await fs.promises.copyFile(item.original_path, item.proposed_target_path);

    logBuffer.push(`"${item.original_path}","${item.proposed_target_path}","SUCCESS",${sourceStats.size},${timestamp}`);
    stats.success++;
    stats.total_bytes += sourceStats.size;
  } catch (e) {
    logBuffer.push(`"${item.original_path}","${item.proposed_target_path}","ERROR",0,${timestamp}`);
    stats.failed++;
  }

  // Flush log buffer periodically
  if (logBuffer.length >= LOG_FLUSH_SIZE) {
    fs.appendFileSync(EXEC_LOG_PATH, logBuffer.join('\n') + '\n');
    logBuffer.length = 0;
  }
}

async function processChunk(items) {
  return Promise.all(items.map(item => copyFile(item)));
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 5.1: COPIA OPTIMIZADA - CHIPRE');
  console.log('═══════════════════════════════════════════════════════════════\n');

  // 1. Load CSV into memory (single read)
  console.log('📋 Cargando plan en memoria...');
  const planContent = fs.readFileSync(REORG_PLAN_PATH, 'utf8');
  const planLines = planContent.split('\n').slice(1);
  
  const cyprusPlan = planLines
    .filter(line => line.trim())
    .map(line => {
      const parts = line.split(',');
      return {
        id: parseInt(parts[0]),
        original_path: parts[1].replace(/"/g, ''),
        proposed_target_path: parts[2].replace(/"/g, ''),
        trip_name: parts[3],
      };
    })
    .filter(item => item.trip_name === TARGET_TRIP);

  console.log(`📸 Fotos de Chipre: ${cyprusPlan.length}`);
  console.log(`⚡ Concurrencia: ${CONCURRENCY} workers\n`);

  // 2. Initialize log file with header
  fs.writeFileSync(EXEC_LOG_PATH, 'original_path,target_path,status,file_size_bytes,timestamp\n');

  // 3. Process in concurrent chunks
  console.log('🔄 Procesando...');
  const chunks = [];
  for (let i = 0; i < cyprusPlan.length; i += CONCURRENCY) {
    chunks.push(cyprusPlan.slice(i, i + CONCURRENCY));
  }

  for (let i = 0; i < chunks.length; i++) {
    await processChunk(chunks[i]);
    if ((i + 1) % 5 === 0) {
      console.log(`  ✅ Procesados: ${Math.min((i + 1) * CONCURRENCY, cyprusPlan.length)}/${cyprusPlan.length}`);
    }
  }

  // 4. Flush remaining logs
  if (logBuffer.length > 0) {
    fs.appendFileSync(EXEC_LOG_PATH, logBuffer.join('\n') + '\n');
  }

  // 5. Final report
  const elapsed = ((Date.now() - stats.start_time) / 1000).toFixed(2);
  
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  REPORTE FINAL - FASE 5.1');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log('📊 RESUMEN:');
  console.log(`   Total archivos: ${cyprusPlan.length}`);
  console.log(`   ✅ Copiados exitosamente: ${stats.success}`);
  console.log(`   ❌ Fallidos: ${stats.failed}`);
  console.log(`   📦 Tamaño total copiado: ${(stats.total_bytes / 1024 / 1024).toFixed(2)} MB`);
  console.log(`   ⏱️  Tiempo total: ${elapsed} segundos`);
  console.log(`   🚀 Velocidad: ${(cyprusPlan.length / parseFloat(elapsed)).toFixed(1)} archivos/segundo`);

  console.log('\n📂 ESTRUCTURA CREADA:');
  console.log(`   ${BASE_TARGET}\\Viajes\\Chipre\\`);
  console.log(`   └── 2023-08\\ (${stats.success} fotos)`);

  console.log('\n📄 Archivo generado:');
  console.log(`   - ${EXEC_LOG_PATH}`);

  console.log('\n✅ Prueba piloto completada exitosamente.');
}

main().catch(console.error);
