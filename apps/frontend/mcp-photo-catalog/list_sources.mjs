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

// Get unique source directories per trip
const tripDirs = {};
for (const line of lines) {
  const parts = parseCSVLine(line);
  const trip = parts[3];
  const src = parts[1];
  
  if (trip === 'Sin_Viaje' || trip === 'cyprus') continue;
  
  const lastSlash = src.lastIndexOf('\\');
  if (lastSlash > 0) {
    const dir = src.substring(0, lastSlash);
    if (!tripDirs[trip]) tripDirs[trip] = new Set();
    tripDirs[trip].add(dir);
  }
}

// Print results
for (const [trip, dirs] of Object.entries(tripDirs)) {
  console.log(`\n=== ${trip} (${dirs.size} directorios) ===`);
  for (const dir of dirs) {
    console.log(`  ${dir}`);
  }
}
