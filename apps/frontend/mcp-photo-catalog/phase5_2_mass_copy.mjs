/**
 * Fase 5.2 - Copiado Masivo de Viajes
 * Copia cada viaje usando robocopy via PowerShell (maneja Unicode/Hebrew)
 * Luego reorganiza en subcarpetas YYYY-MM según el plan
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const TRIP_MAP = {
  'argentina-2011': {
    folder: 'Argentina_2011',
    sources: ['F:\\2011\\Noviembre\\טיול לארגנטינה'],
  },
  'argentina-2025': {
    folder: 'Argentina_2025',
    sources: [
      'F:\\2025\\Septiembre\\Viaje Familiar de 30 dias por Argentina',
      'F:\\2025\\Octubre\\Viaje Familiar de 30 dias por Argentina',
    ],
  },
  'slovenia-2015': {
    folder: 'Eslovenia_2015',
    sources: ['F:\\2015\\Julio\\טיול בסלובניה'],
  },
  'italy-2023': {
    folder: 'Italia_2023',
    sources: [
      'F:\\2023\\Octubre\\גברים רעבים באיטליה-2023',
      'F:\\2023\\Noviembre\\גברים רעבים באיטליה-2023',
      'F:\\2023\\Diciembre\\גברים רעבים באיטליה-2023',
    ],
  },
  'crete-2013': {
    folder: 'Creta_2013',
    sources: ['F:\\2013\\Julio\\טיול לכרתים'],
  },
  'croatia-montenegro-2010': {
    folder: 'Croacia_Montenegro_2010',
    sources: ['F:\\2010\\Junio\\טיול משק למונטנגרו'],
  },
  'bosnia-2023': {
    folder: 'Bosnia_2023',
    sources: [
      'F:\\2023\\Mayo\\בוסניה',
      'F:\\2023\\Abril\\בוסניה',
    ],
  },
  'denmark-2024': {
    folder: 'Dinamarca_2024',
    sources: ['F:\\2024\\Julio'],
  },
};

const BASE_TARGET = 'F:\\Fotos_Organizadas\\Viajes';
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

function copyTrip(tripKey, config) {
  const targetDir = path.join(BASE_TARGET, config.folder);
  
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  COPIANDO: ${config.folder}`);
  console.log(`${'═'.repeat(60)}`);
  
  // Create target directory
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }
  
  let totalCopied = 0;
  let totalFailed = 0;
  
  for (const source of config.sources) {
    if (!fs.existsSync(source)) {
      console.log(`  ⚠️  Fuente no encontrada: ${source}`);
      continue;
    }
    
    console.log(`  📁 Copiando desde: ${source}`);
    
    // Use robocopy via PowerShell to handle Unicode paths
    const psCmd = `powershell -Command "robocopy '${source}' '${targetDir}' /E /COPY:DAT /R:1 /W:1 /MT:8 /NP"`;
    
    try {
      const result = execSync(psCmd, { 
        encoding: 'utf8', 
        timeout: 1800000,
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      // Parse robocopy output for stats
      const lines = result.split('\n');
      for (const line of lines) {
        if (line.includes('Files :')) {
          const match = line.match(/Files\s*:\s*(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+(\d+)/);
          if (match) {
            totalCopied += parseInt(match[2]);
            totalFailed += parseInt(match[4]);
          }
        }
      }
    } catch (e) {
      console.log(`  ❌ Error copiando: ${e.message}`);
    }
  }
  
  console.log(`  ✅ ${config.folder}: ${totalCopied} copiados, ${totalFailed} fallidos`);
  
  return { copied: totalCopied, failed: totalFailed };
}

function reorganizeByDate(tripKey, config) {
  const targetDir = path.join(BASE_TARGET, config.folder);
  
  console.log(`\n  📅 Reorganizando ${config.folder} en subcarpetas YYYY-MM...`);
  
  // Read plan for this trip
  const csv = fs.readFileSync('./reorganization_plan.csv', 'utf8');
  const lines = csv.split('\n').filter(l => l.trim());
  
  let reorganized = 0;
  
  for (const line of lines) {
    const parts = parseCSVLine(line);
    const trip = parts[3];
    const srcPath = parts[1];
    const dstPath = parts[2];
    
    if (trip !== tripKey) continue;
    
    // Extract YYYY-MM from date in filename or path
    const dateMatch = srcPath.match(/(\d{4})-(\d{2})/);
    if (!dateMatch) continue;
    
    const yearMonth = `${dateMatch[1]}-${dateMatch[2]}`;
    const filename = path.basename(srcPath);
    const targetPath = path.join(targetDir, yearMonth, filename);
    
    // Check if file exists in flat directory
    const flatPath = path.join(targetDir, filename);
    if (fs.existsSync(flatPath) && !fs.existsSync(targetPath)) {
      const dir = path.dirname(targetPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.renameSync(flatPath, targetPath);
      reorganized++;
    }
  }
  
  console.log(`  ✅ ${reorganized} archivos reorganizados`);
  return reorganized;
}

// Main execution
console.log('═══════════════════════════════════════════════════════════════');
console.log('  FASE 5.2: COPIADO MASIVO DE VIAJES');
console.log('═══════════════════════════════════════════════════════════════');

const results = {};
const startTime = Date.now();

for (const [tripKey, config] of Object.entries(TRIP_MAP)) {
  const result = copyTrip(tripKey, config);
  results[tripKey] = { ...config, ...result };
}

// Reorganize all trips by date
console.log(`\n${'═'.repeat(60)}`);
console.log('  REORGANIZACIÓN POR FECHAS');
console.log(`${'═'.repeat(60)}`);

for (const [tripKey, config] of Object.entries(TRIP_MAP)) {
  reorganizeByDate(tripKey, config);
}

const endTime = Date.now();
const elapsed = Math.floor((endTime - startTime) / 1000);

// Generate summary
console.log(`\n${'═'.repeat(60)}`);
console.log('  RESUMEN FINAL');
console.log(`${'═'.repeat(60)}`);
console.log('');
console.log('Viaje'.padEnd(35) + 'Esperadas'.padEnd(12) + 'Copiadas'.padEnd(12) + 'Errores');
console.log('─'.repeat(70));

let totalExpected = 0;
let totalCopied = 0;
let totalFailed = 0;

for (const [tripKey, data] of Object.entries(results)) {
  const expected = data.copied + data.failed;
  totalExpected += expected;
  totalCopied += data.copied;
  totalFailed += data.failed;
  console.log(
    data.folder.padEnd(35) +
    expected.toString().padEnd(12) +
    data.copied.toString().padEnd(12) +
    data.failed
  );
}

console.log('─'.repeat(70));
console.log('TOTAL'.padEnd(35) + totalExpected.toString().padEnd(12) + totalCopied.toString().padEnd(12) + totalFailed);
console.log('');
console.log(`⏱️  Tiempo total: ${elapsed} segundos`);
console.log('');

// Write log
const logHeader = 'trip_folder,expected,copied,failed,timestamp\n';
const logRows = Object.values(results).map(d => 
  `${d.folder},${d.copied + d.failed},${d.copied},${d.failed},${new Date().toISOString()}`
).join('\n');
fs.writeFileSync(LOG_FILE, logHeader + logRows);
console.log(`📄 Log guardado en: ${LOG_FILE}`);
