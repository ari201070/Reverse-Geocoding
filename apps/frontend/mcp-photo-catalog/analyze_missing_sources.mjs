import fs from 'fs';
import path from 'path';

/**
 * Analiza los 1.313 archivos cuyo origen no existe en disco.
 * Agrupa por unidad y ruta principal para identificar el origen.
 */

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

console.log('📖 Leyendo plan...');
const csv = fs.readFileSync(REORG_PLAN, 'utf8');
const lines = csv.split('\n').filter(l => l.trim());
const dataLines = lines.slice(1);

// ALL entries (including Sin_Viaje) for full picture of missing sources
const allLines = dataLines.filter(l => {
  const parts = parseCSVLine(l);
  return parts[3] && parts[3] !== 'trip';
});

console.log(`🔍 Verificando ${allLines.length} entradas en el plan...`);

const missingByDrive = {};
const missingByTrip = {};
const missingDetails = [];

let totalChecked = 0;
for (const line of allLines) {
  const parts = parseCSVLine(line);
  const src = parts[1];
  const trip = parts[3];
  
  try {
    fs.accessSync(src, fs.constants.F_OK);
  } catch (e) {
    // File is missing
    totalChecked++;
    
    // Get drive letter or UNC root
    const driveMatch = src.match(/^([A-Za-z]:\\)/);
    const drive = driveMatch ? driveMatch[1].toUpperCase() : 'UNKNOWN';
    
    // Get second level path (e.g., F:\2011\Enero -> F:\2011)
    const parts2 = src.split('\\');
    const topLevel = parts2.length >= 3 ? `${parts2[0]}\\${parts2[1]}\\${parts2[2]}` : src;

    if (!missingByDrive[drive]) missingByDrive[drive] = 0;
    missingByDrive[drive]++;

    if (!missingByTrip[trip]) missingByTrip[trip] = {};
    if (!missingByTrip[trip][drive]) missingByTrip[trip][drive] = 0;
    missingByTrip[trip][drive]++;

    missingDetails.push({ src, trip, drive, topLevel });
  }
}

// Group missing sources by topLevel folder for a clear picture
const byTopLevel = {};
for (const d of missingDetails) {
  if (!byTopLevel[d.topLevel]) byTopLevel[d.topLevel] = { count: 0, trips: {} };
  byTopLevel[d.topLevel].count++;
  if (!byTopLevel[d.topLevel].trips[d.trip]) byTopLevel[d.topLevel].trips[d.trip] = 0;
  byTopLevel[d.topLevel].trips[d.trip]++;
}

// Sort by count
const sortedTopLevel = Object.entries(byTopLevel).sort((a, b) => b[1].count - a[1].count);

const report = {
  totalFaltantes: totalChecked,
  porUnidad: missingByDrive,
  porViaje: missingByTrip,
  top20CarpetasOrigen: sortedTopLevel.slice(0, 20).map(([path, data]) => ({ path, ...data }))
};

fs.writeFileSync('missing_sources_report.json', JSON.stringify(report, null, 2));

console.log('\n========================================');
console.log(`📊 ANÁLISIS DE FUENTES FALTANTES`);
console.log('========================================');
console.log(`\nTotal archivos faltantes en origen: ${totalChecked}\n`);
console.log('Por unidad de disco:');
for (const [drive, count] of Object.entries(missingByDrive).sort()) {
  console.log(`  ${drive} → ${count} archivos`);
}
console.log('\nTop 20 carpetas de origen ausentes:');
for (const [topPath, data] of sortedTopLevel.slice(0, 20)) {
  console.log(`  [${data.count}] ${topPath}`);
}
console.log('\nReporte completo guardado en missing_sources_report.json');
