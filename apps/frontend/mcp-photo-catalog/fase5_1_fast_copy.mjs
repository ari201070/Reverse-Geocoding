/**
 * Fase 5.1: Copia rápida de Chipre (versión optimizada)
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const REORG_PLAN_PATH = './reorganization_plan.csv';
const EXEC_LOG_PATH = './execution_log.csv';
const BASE_TARGET = 'F:\\Fotos_Organizadas';
const TARGET_TRIP = 'cyprus';

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 5.1: COPIA RÁPIDA - CHIPRE');
  console.log('═══════════════════════════════════════════════════════════════\n');

  // Read reorganization plan
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

  console.log(`📸 Fotos de Chipre a copiar: ${cyprusPlan.length}\n`);

  // Initialize execution log
  const logLines = ['original_path,target_path,status,file_size_bytes,timestamp'];

  const stats = { success: 0, failed: 0, total_bytes: 0 };

  for (let i = 0; i < cyprusPlan.length; i++) {
    const item = cyprusPlan[i];
    const timestamp = new Date().toISOString();

    try {
      if (!fs.existsSync(item.original_path)) {
        logLines.push(`"${item.original_path}","${item.proposed_target_path}","FILE_NOT_FOUND",0,${timestamp}`);
        stats.failed++;
        continue;
      }

      const sourceStats = fs.statSync(item.original_path);
      
      // Create target directory
      const targetDir = path.dirname(item.proposed_target_path);
      if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
      }

      // Copy file
      fs.copyFileSync(item.original_path, item.proposed_target_path);

      logLines.push(`"${item.original_path}","${item.proposed_target_path}","SUCCESS",${sourceStats.size},${timestamp}`);
      stats.success++;
      stats.total_bytes += sourceStats.size;

      if (stats.success % 10 === 0) {
        console.log(`  ✅ [${stats.success}/${cyprusPlan.length}] Copied`);
      }
    } catch (e) {
      logLines.push(`"${item.original_path}","${item.proposed_target_path}","ERROR",0,${timestamp}`);
      stats.failed++;
    }
  }

  // Write execution log
  fs.writeFileSync(EXEC_LOG_PATH, logLines.join('\n'));

  // Report
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  REPORTE - FASE 5.1');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log('📊 RESUMEN:');
  console.log(`   Total archivos: ${cyprusPlan.length}`);
  console.log(`   ✅ Copiados exitosamente: ${stats.success}`);
  console.log(`   ❌ Fallidos: ${stats.failed}`);
  console.log(`   📦 Tamaño total copiado: ${(stats.total_bytes / 1024 / 1024).toFixed(2)} MB`);

  console.log('\n📂 ESTRUCTURA CREADA:');
  console.log(`   ${BASE_TARGET}\\Viajes\\Chipre\\`);
  console.log(`   └── 2023-08\\ (${stats.success} fotos)`);

  console.log('\n📄 Archivo generado:');
  console.log(`   - ${EXEC_LOG_PATH}`);

  console.log('\n✅ Prueba piloto completada.');
}

main().catch(console.error);
