import fs from 'fs';

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

const csv = fs.readFileSync('./reorganization_plan.csv', 'utf8');
const lines = csv.split('\n').filter(l => l.trim());

// Count files per trip that come from each top-level source directory
const TRIP_MAIN_SOURCES = {
  'argentina-2011': 'F:\\2011\\Noviembre\\טיול לארגנטינה',
  'argentina-2025': 'F:\\2025\\Septiembre\\Viaje Familiar de 30 dias por Argentina',
  'slovenia-2015': 'F:\\2015\\Julio\\טיול בסלובניה',
  'italy-2023': 'F:\\2023\\Octubre\\גברים רעבים באיטליה-2023',
  'crete-2013': 'F:\\2013\\Julio\\טיול לכרתים',
  'croatia-montenegro-2010': 'F:\\2010\\Junio\\טיול משק למונטנגרו',
  'bosnia-2023': 'F:\\2023\\Mayo\\בוסניה',
  'denmark-2024': 'F:\\2024\\Julio',
};

for (const [trip, mainSource] of Object.entries(TRIP_MAIN_SOURCES)) {
  let fromMain = 0;
  let total = 0;
  
  for (const line of lines) {
    const parts = parseCSVLine(line);
    if (parts[3] !== trip) continue;
    total++;
    if (parts[1].startsWith(mainSource)) fromMain++;
  }
  
  const pct = total > 0 ? Math.round(fromMain / total * 100) : 0;
  console.log(`${trip}: ${fromMain}/${total} (${pct}%) desde ${mainSource}`);
}
