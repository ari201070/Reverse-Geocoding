import Database from 'better-sqlite3';

const db = new Database('C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db');

const noCountry = db.prepare("SELECT file_path, date_taken FROM photos WHERE country IS NULL OR country = ''").all();

// Analyze by year
const yearStats = {};
for (const p of noCountry) {
  const match = p.file_path.match(/F:[\\/](\d{4})/);
  const year = match ? match[1] : 'Unknown';
  if (!yearStats[year]) yearStats[year] = 0;
  yearStats[year]++;
}

console.log('=== DISTRIBUCIÓN POR AÑO ===');
console.log('Total fotos sin country:', noCountry.length);
console.log('');

const sortedYears = Object.entries(yearStats).sort((a, b) => a[0].localeCompare(b[0]));
for (const [year, count] of sortedYears) {
  const bar = '█'.repeat(Math.ceil(count / 50));
  console.log(year + ': ' + count.toString().padStart(5) + ' ' + bar);
}

// Analyze by month
console.log('\n=== DISTRIBUCIÓN POR MES (AÑO-MES) ===');
const monthStats = {};
for (const p of noCountry) {
  const match = p.file_path.match(/F:[\\/](\d{4})[\\/](\w+)/);
  if (match) {
    const key = match[1] + '-' + match[2];
    if (!monthStats[key]) monthStats[key] = 0;
    monthStats[key]++;
  }
}

const sortedMonths = Object.entries(monthStats).sort((a, b) => a[0].localeCompare(b[0]));
for (const [month, count] of sortedMonths) {
  if (count >= 50) {
    console.log(month + ': ' + count.toString().padStart(5));
  }
}

// Analyze by specific folder
console.log('\n=== CARPETAS CON MÁS FOTOS SIN COUNTRY ===');
const folderStats = {};
for (const p of noCountry) {
  const lastBS = p.file_path.lastIndexOf('\\');
  const lastFS = p.file_path.lastIndexOf('/');
  const idx = Math.max(lastBS, lastFS);
  const folder = idx > 0 ? p.file_path.substring(0, idx) : 'Root';
  if (!folderStats[folder]) folderStats[folder] = 0;
  folderStats[folder]++;
}

const sortedFolders = Object.entries(folderStats).sort((a, b) => b[1] - a[1]);
for (const [folder, count] of sortedFolders.slice(0, 20)) {
  console.log(count.toString().padStart(5) + '  ' + folder);
}

db.close();
