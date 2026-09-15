import Database from 'better-sqlite3';

const db = new Database('C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db');

const allPhotos = db.prepare('SELECT id, file_path, country, latitude FROM photos').all();
const folderMap = new Map();

for (const p of allPhotos) {
  const idx = Math.max(p.file_path.lastIndexOf('\\'), p.file_path.lastIndexOf('/'));
  if (idx < 0) continue;
  const folder = p.file_path.substring(0, idx);
  
  if (!folderMap.has(folder)) folderMap.set(folder, { gps: 0, noGps: 0, country: 0 });
  const f = folderMap.get(folder);
  if (p.latitude) f.gps++;
  else f.noGps++;
  if (p.country && p.country !== '') f.country++;
}

let foldersWithBoth = 0;
let targets = 0;
for (const [, s] of folderMap) {
  if (s.gps > 0 && s.noGps > 0) {
    foldersWithBoth++;
    targets += s.noGps;
  }
}

console.log('Folders:', folderMap.size);
console.log('Folders with GPS + non-GPS:', foldersWithBoth);
console.log('Non-GPS photos resolvable:', targets);

db.close();
