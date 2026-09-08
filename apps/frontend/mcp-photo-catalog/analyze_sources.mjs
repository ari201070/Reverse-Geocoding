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

const tripSources = {};
const tripCounts = {};

for (const line of lines) {
    const parts = parseCSVLine(line);
    const trip = parts[3];
    const src = parts[1];
    if (trip === 'Sin_Viaje' || trip === 'cyprus') continue;
    
    const lastSlash = src.lastIndexOf('\\');
    const srcDir = src.substring(0, lastSlash);
    if (!tripSources[trip]) tripSources[trip] = new Set();
    tripSources[trip].add(srcDir);
    tripCounts[trip] = (tripCounts[trip] || 0) + 1;
}

for (const [trip, dirs] of Object.entries(tripSources)) {
    console.log(`\n=== ${trip} (${tripCounts[trip]} fotos) ===`);
    for (const dir of dirs) {
        console.log(`  ${dir}`);
    }
}
