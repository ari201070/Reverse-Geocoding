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

// Skip header (id,src,dst,trip)
const dataLines = lines.slice(1);

// Only process trips (not Sin_Viaje, not cyprus or Chipre)
// The JSON shows Chipre and Cyprus might be mixed, let's filter what the user originally filtered.
const tripLines = dataLines.filter(l => {
  const parts = parseCSVLine(l);
  const trip = parts[3];
  return trip !== 'Sin_Viaje' && trip !== 'cyprus' && trip !== 'Chipre' && trip !== 'trip';
});

console.log(`Procesando ${tripLines.length} archivos de viajes para auditoria...`);

const report = {};
let totalCompletados = 0;
let totalPendientes = 0;
let totalIncompletos = 0;
let totalFaltantesSrc = 0;

for (let i = 0; i < tripLines.length; i++) {
  const parts = parseCSVLine(tripLines[i]);
  const src = parts[1];
  const dst = parts[2];
  const trip = parts[3];
  
  if (!report[trip]) {
    report[trip] = {
      completados: 0,
      pendientes: 0,
      incompletos: 0,
      faltantesSrc: 0,
      total: 0
    };
  }
  
  report[trip].total++;
  
  let srcSize = -1;
  try {
    const srcStat = fs.statSync(src);
    srcSize = srcStat.size;
  } catch (e) {
    report[trip].faltantesSrc++;
    totalFaltantesSrc++;
    continue;
  }
  
  try {
    const dstStat = fs.statSync(dst);
    const dstSize = dstStat.size;
    
    if (dstSize === srcSize) {
      report[trip].completados++;
      totalCompletados++;
    } else {
      report[trip].incompletos++;
      totalIncompletos++;
    }
  } catch (e) {
    report[trip].pendientes++;
    totalPendientes++;
  }
}

const output = {
  resumenGlobal: {
    totalArchivosPrevistos: tripLines.length,
    completados: totalCompletados,
    pendientes: totalPendientes,
    incompletos: totalIncompletos,
    faltantesEnOrigen: totalFaltantesSrc
  },
  porViaje: report
};

fs.writeFileSync('audit_report.json', JSON.stringify(output, null, 2));
console.log('Auditoria completada. Resultados en audit_report.json');
