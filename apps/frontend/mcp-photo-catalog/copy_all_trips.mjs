/**
 * Fase 5.2 - Copia masiva usando plan reorganizado
 * Copia CADA archivo individualmente del plan al destino correcto
 */

import fs from 'fs';
import path from 'path';

const REORG_PLAN = './reorganization_plan.csv';
const BASE_TARGET = 'F:\\Fotos_Organizadas';
const LOG_FILE = './execution_log.csv';

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') inQuotes = !inQuotes;
    else if (char === ',' && !inQuotes) { result.push(current); current = ''; }
    else current += char;
  }
  result.push(current);
  return result;
}

console.log('═══════════════════════════════════════════════════════════════');
console.log('  FASE 5.2 - COPIA MASIVA DESDE PLAN');
console.log('═══════════════════════════════════════════════════════════════\n');

const csv = fs.readFileSync(REORG_PLAN, 'utf8');
const lines = csv.split('\n').filter(l => l.trim());

// Skip cyprus (already done)
const planLines = lines.filter(l => !l.includes(',cyprus,'));

console.log(`📋 Plan: ${planLines.length} archivos (excl. Chipre)\n`);

const results = {};
let totalCopied = 0;
let totalFailed = 0;
let totalSkipped = 0;

for (let i = 0; i < planLines.length; i++) {
  const parts = parseCSVLine(planLines[i]);
  const id = parts[0];
  const src = parts[1];
  const dst = parts[2];
  const trip = parts[3];
  
  // Initialize trip counter
  if (!results[trip]) results[trip] = { copied: 0, failed: 0, skipped: 0 };
  
  // Skip if already exists
  if (fs.existsSync(dst)) {
    results[trip].skipped++;
    totalSkipped++;
    continue;
  }
  
  // Check source exists
  if (!fs.existsSync(src)) {
    results[trip].failed++;
    totalFailed++;
    continue;
  }
  
  // Create target directory
  const dstDir = path.dirname(dst);
  if (!fs.existsSync(dstDir)) {
    fs.mkdirSync(dstDir, { recursive: true });
  }
  
  // Copy file
  try {
    fs.copyFileSync(src, dst);
    results[trip].copied++;
    totalCopied++;
    
    if (totalCopied % 100 === 0) {
      console.log(`  ✅ ${totalCopied.toLocaleString()} copiados...`);
    }
  } catch (e) {
    results[trip].failed++;
    totalFailed++;
  }
}

console.log('\n═══════════════════════════════════════════════════════════════');
console.log('  RESUMEN POR VIAJE');
console.log('═══════════════════════════════════════════════════════════════\n');

console.log('Viaje'.padEnd(30) + 'Copiados'.padEnd(12) + 'Fallidos'.padEnd(12) + 'Saltados');
console.log('─'.repeat(70));

const tripMap = {
  'argentina-2011': 'Argentina_2011',
  'argentina-2025': 'Argentina_2025',
  'slovenia-2015': 'Eslovenia_2015',
  'italy-2023': 'Italia_2023',
  'crete-2013': 'Creta_2013',
  'croatia-montenegro-2010': 'Croacia_Montenegro_2010',
  'bosnia-2023': 'Bosnia_2023',
  'denmark-2024': 'Dinamarca_2024',
  'Sin_Viaje': 'Sin_Viaje',
};

for (const [trip, data] of Object.entries(results).sort((a, b) => b[1].copied - a[1].copied)) {
  const name = tripMap[trip] || trip;
  console.log(
    name.padEnd(30) +
    data.copied.toString().padEnd(12) +
    data.failed.toString().padEnd(12) +
    data.skipped
  );
}

console.log('─'.repeat(70));
console.log('TOTAL'.padEnd(30) + totalCopied.toString().padEnd(12) + totalFailed.toString().padEnd(12) + totalSkipped);

// Write log
const logHeader = 'trip,trip_folder,copied,failed,skipped,timestamp\n';
const logRows = Object.entries(results).map(([trip, data]) => 
  `${trip},${tripMap[trip] || trip},${data.copied},${data.failed},${data.skipped},${new Date().toISOString()}`
).join('\n');
fs.writeFileSync(LOG_FILE, logHeader + logRows);

console.log(`\n📄 Log: ${LOG_FILE}`);
