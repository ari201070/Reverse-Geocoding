/**
 * Copia masiva simplificada - solo archivos de viajes (no Sin_Viaje)
 */

import fs from 'fs';
import path from 'path';

const REORG_PLAN = './reorganization_plan.csv';

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

const csv = fs.readFileSync(REORG_PLAN, 'utf8');
const lines = csv.split('\n').filter(l => l.trim());

// Only process trips (not Sin_Viaje, not cyprus)
const tripLines = lines.filter(l => {
  const parts = parseCSVLine(l);
  return parts[3] !== 'Sin_Viaje' && parts[3] !== 'cyprus';
});

console.log(`📋 Procesando ${tripLines.length} archivos de viajes...\n`);

let copied = 0;
let failed = 0;
let skipped = 0;

for (let i = 0; i < tripLines.length; i++) {
  const parts = parseCSVLine(tripLines[i]);
  const src = parts[1];
  const dst = parts[2];
  
  // Skip if already exists
  if (fs.existsSync(dst)) {
    skipped++;
    continue;
  }
  
  // Check source
  if (!fs.existsSync(src)) {
    failed++;
    continue;
  }
  
  // Create dir
  const dstDir = path.dirname(dst);
  if (!fs.existsSync(dstDir)) {
    fs.mkdirSync(dstDir, { recursive: true });
  }
  
  // Copy
  try {
    fs.copyFileSync(src, dst);
    copied++;
    
    if (copied % 500 === 0) {
      console.log(`  ✅ ${copied.toLocaleString()} copiados...`);
    }
  } catch (e) {
    failed++;
  }
}

console.log(`\n✅ completado: ${copied.toLocaleString()} copiados, ${failed} fallidos, ${skipped} saltados`);
