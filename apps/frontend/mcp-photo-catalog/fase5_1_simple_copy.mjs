/**
 * Fase 5.1: Copia simple y rápida de Chipre
 */

import fs from 'fs';
import path from 'path';

const REORG_PLAN_PATH = './reorganization_plan.csv';
const EXEC_LOG_PATH = './execution_log.csv';
const TARGET_TRIP = 'cyprus';

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 5.1: COPIA SIMPLE - CHIPRE');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const startTime = Date.now();

  // Load plan
  const planContent = fs.readFileSync(REORG_PLAN_PATH, 'utf8');
  const planLines = planContent.split('\n').slice(1);
  
  const cyprusPlan = planLines
    .filter(line => line.trim())
    .map(line => {
      const parts = line.split(',');
      return {
        original_path: parts[1].replace(/"/g, ''),
        proposed_target_path: parts[2].replace(/"/g, ''),
        trip_name: parts[3],
      };
    })
    .filter(item => item.trip_name === TARGET_TRIP);

  console.log(`📸 Fotos de Chipre: ${cyprusPlan.length}\n`);

  // Init log
  const logLines = ['original_path,target_path,status,file_size_bytes'];

  let success = 0, failed = 0, totalBytes = 0;

  for (let i = 0; i < cyprusPlan.length; i++) {
    const item = cyprusPlan[i];

    try {
      if (!fs.existsSync(item.original_path)) {
        logLines.push(`"${item.original_path}","${item.proposed_target_path}","FILE_NOT_FOUND",0`);
        failed++;
        continue;
      }

      const stats = fs.statSync(item.original_path);
      const dir = path.dirname(item.proposed_target_path);
      
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      fs.copyFileSync(item.original_path, item.proposed_target_path);

      logLines.push(`"${item.original_path}","${item.proposed_target_path}","SUCCESS",${stats.size}`);
      success++;
      totalBytes += stats.size;

      if (success % 20 === 0) {
        console.log(`  ✅ [${success}/${cyprusPlan.length}] Copied`);
      }
    } catch (e) {
      logLines.push(`"${item.original_path}","${item.proposed_target_path}","ERROR",0`);
      failed++;
    }
  }

  // Write log
  fs.writeFileSync(EXEC_LOG_PATH, logLines.join('\n'));

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  REPORTE FINAL');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log('📊 RESUMEN:');
  console.log(`   Total archivos: ${cyprusPlan.length}`);
  console.log(`   ✅ Copiados: ${success}`);
  console.log(`   ❌ Fallidos: ${failed}`);
  console.log(`   📦 Tamaño total: ${(totalBytes / 1024 / 1024).toFixed(2)} MB`);
  console.log(`   ⏱️  Tiempo: ${elapsed} segundos`);
  console.log(`   🚀 Velocidad: ${(cyprusPlan.length / parseFloat(elapsed)).toFixed(1)} archivos/segundo`);

  console.log('\n📄 Log generado: execution_log.csv');
  console.log('\n✅ Completado.');
}

main().catch(console.error);
