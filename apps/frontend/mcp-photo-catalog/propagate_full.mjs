import Database from 'better-sqlite3';

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';

const PATH_KEYWORDS = [
  { regex: /פיזה|pisa/i, city: 'Pisa', country: 'Italy' },
  { regex: /רומא|roma|rome/i, city: 'Rome', country: 'Italy' },
  { regex: /ונציה|venecia|venice/i, city: 'Venice', country: 'Italy' },
  { regex: /פירנצה|florencia|florence/i, city: 'Florence', country: 'Italy' },
  { regex: /מילאנו|milan/i, city: 'Milan', country: 'Italy' },
  { regex: /איטליה|italia|italy/i, country: 'Italy' },
  { regex: /ארגנטינה|argentina/i, country: 'Argentina' },
  { regex: /ברילוצ'ה|bariloche/i, city: 'Bariloche', country: 'Argentina' },
  { regex: /מנדוזה|mendoza/i, city: 'Mendoza', country: 'Argentina' },
  { regex: /איגואסו|iguazu/i, city: 'Iguazú', country: 'Argentina' },
  { regex: /בואנוס איירס|buenos aires/i, city: 'Buenos Aires', country: 'Argentina' },
  { regex: /ספרד|españa|spain/i, country: 'Spain' },
  { regex: /צרפת|francia|france/i, country: 'France' },
  { regex: /גרמניה|alemania|germany/i, country: 'Germany' },
  { regex: /בוסניה|bosnia/i, country: 'Bosnia and Herzegovina' },
  { regex: /סרajeבו|sarajevo/i, city: 'Sarajevo', country: 'Bosnia and Herzegovina' },
  { regex: /יוון|grecia|greece/i, country: 'Greece' },
  { regex: /כרתים|crete/i, city: 'Crete', country: 'Greece' },
  { regex: /סלובניה|slovenia/i, country: 'Slovenia' },
  { regex: /קרואטיה|croatia/i, country: 'Croatia' },
  { regex: /דנמרק|denmark/i, country: 'Denmark' },
  { regex: /קופנהגן|copenhagen/i, city: 'Copenhagen', country: 'Denmark' },
  { regex: /תאילנד|tailandia|thailand/i, country: 'Thailand' },
  { regex: /יפן|japon|japan/i, country: 'Japan' },
  { regex: /מרוקו|marruecos|morocco/i, country: 'Morocco' },
  { regex: /ברזיל|brasil|brazil/i, country: 'Brazil' },
  { regex: /ארצות הברית|usa|eeuu/i, country: 'United States' },
  { regex: /אנגליה|england|uk/i, country: 'United Kingdom' },
];

const KNOWN_TRIPS = [
  { country: 'Italy', start: '2023-10-03', end: '2023-10-11' },
  { country: 'Argentina', start: '2025-02-01', end: '2025-02-28' },
  { country: 'Argentina', start: '2011-11-07', end: '2012-02-06' },
  { country: 'Slovenia', start: '2015-08-01', end: '2015-08-15' },
  { country: 'Croatia', start: '2010-08-01', end: '2010-08-20' },
  { country: 'Greece', start: '2013-07-20', end: '2013-07-30' },
  { country: 'Bosnia and Herzegovina', start: '2023-09-01', end: '2023-09-10' },
  { country: 'Denmark', start: '2024-07-01', end: '2024-07-15' },
];

function getFolder(filePath) {
  const lastBS = filePath.lastIndexOf('\\');
  const lastFS = filePath.lastIndexOf('/');
  const idx = Math.max(lastBS, lastFS);
  return idx > 0 ? filePath.substring(0, idx) : null;
}

async function main() {
  const db = new Database(DB_PATH);
  
  const total = db.prepare('SELECT COUNT(*) as c FROM photos').get().c;
  console.log('Total photos:', total);

  // PHASE 0: Clear everything
  console.log('\n--- PHASE 0: Clear all country/city ---');
  db.prepare('UPDATE photos SET country = NULL, city = NULL').run();
  console.log('Cleared all country/city');

  // PHASE 1: Israel GPS (lat 29-33, lon 34-36)
  console.log('\n--- PHASE 1: Israel GPS ---');
  const israelGPS = db.prepare(
    "UPDATE photos SET country = 'Israel', city = 'Israel' WHERE latitude BETWEEN 29 AND 33 AND longitude BETWEEN 34 AND 36"
  ).run();
  console.log('Israel GPS:', israelGPS.changes);

  // PHASE 2: Path keywords
  console.log('\n--- PHASE 2: Path keywords ---');
  const allPhotos = db.prepare('SELECT id, file_path, country, city FROM photos').all();
  const updatePath = db.prepare('UPDATE photos SET country = ?, city = COALESCE(?, city) WHERE id = ?');
  let pathUpdates = 0;

  db.transaction(() => {
    for (const row of allPhotos) {
      if (!row.file_path) continue;
      for (const kw of PATH_KEYWORDS) {
        if (kw.regex.test(row.file_path)) {
          if (kw.country) {
            updatePath.run(kw.country, kw.city || null, row.id);
            pathUpdates++;
          }
          break;
        }
      }
    }
  })();
  console.log('Path keyword updates:', pathUpdates);

  // PHASE 3: Sister folder (GPS-equipped siblings)
  console.log('\n--- PHASE 3: Sister folder propagation ---');
  const refreshed = db.prepare('SELECT id, file_path, country, city, latitude FROM photos').all();
  
  const folderMap = new Map();
  for (const p of refreshed) {
    const folder = getFolder(p.file_path);
    if (!folder) continue;
    if (!folderMap.has(folder)) folderMap.set(folder, []);
    folderMap.get(folder).push(p);
  }

  const updateFolder = db.prepare('UPDATE photos SET country = ?, city = COALESCE(?, city) WHERE id = ?');
  let folderUpdates = 0;

  db.transaction(() => {
    for (const [, photos] of folderMap) {
      const source = photos.find(p => p.latitude && p.country && p.country !== '');
      if (!source) continue;
      
      for (const p of photos) {
        if (p.id === source.id) continue;
        if (!p.country || p.country === '') {
          updateFolder.run(source.country, source.city, p.id);
          folderUpdates++;
        }
      }
    }
  })();
  console.log('Folder propagation updates:', folderUpdates);

  // PHASE 4: KnownTrips
  console.log('\n--- PHASE 4: KnownTrips ---');
  const updateTrip = db.prepare(
    "UPDATE photos SET country = ? WHERE DATE(date_taken) BETWEEN DATE(?) AND DATE(?) AND (country IS NULL OR country = '')"
  );
  let tripUpdates = 0;
  db.transaction(() => {
    for (const trip of KNOWN_TRIPS) {
      tripUpdates += updateTrip.run(trip.country, trip.start, trip.end).changes;
    }
  })();
  console.log('KnownTrips updates:', tripUpdates);

  // PHASE 5: Second pass - folder propagation from newly classified
  console.log('\n--- PHASE 5: Second pass folder propagation ---');
  const refreshed2 = db.prepare('SELECT id, file_path, country, city, latitude FROM photos').all();
  const folderMap2 = new Map();
  for (const p of refreshed2) {
    const folder = getFolder(p.file_path);
    if (!folder) continue;
    if (!folderMap2.has(folder)) folderMap2.set(folder, []);
    folderMap2.get(folder).push(p);
  }

  let folderUpdates2 = 0;
  db.transaction(() => {
    for (const [, photos] of folderMap2) {
      const source = photos.find(p => p.country && p.country !== '');
      if (!source) continue;
      
      for (const p of photos) {
        if (p.id === source.id) continue;
        if (!p.country || p.country === '') {
          updateFolder.run(source.country, source.city, p.id);
          folderUpdates2++;
        }
      }
    }
  })();
  console.log('Second pass folder updates:', folderUpdates2);

  // FINAL STATS
  console.log('\n═══════════════════════════════════════════════════');
  console.log('FINAL RESULTS');
  console.log('═══════════════════════════════════════════════════');
  
  const stats = {
    total: db.prepare('SELECT COUNT(*) as c FROM photos').get().c,
    withCountry: db.prepare("SELECT COUNT(*) as c FROM photos WHERE country IS NOT NULL AND country != ''").get().c,
    withCity: db.prepare("SELECT COUNT(*) as c FROM photos WHERE city IS NOT NULL AND city != ''").get().c,
    noCountry: db.prepare("SELECT COUNT(*) as c FROM photos WHERE country IS NULL OR country = ''").get().c,
  };

  console.log(`Total: ${stats.total}`);
  console.log(`With country: ${stats.withCountry} (${((stats.withCountry/stats.total)*100).toFixed(1)}%)`);
  console.log(`With city: ${stats.withCity} (${((stats.withCity/stats.total)*100).toFixed(1)}%)`);
  console.log(`No country: ${stats.noCountry}`);

  const countries = db.prepare("SELECT country, COUNT(*) as c FROM photos WHERE country IS NOT NULL AND country != '' GROUP BY country ORDER BY c DESC").all();
  console.log('\nCountry distribution:');
  countries.forEach(c => console.log(`  ${c.country}: ${c.c}`));

  // Sample verification
  console.log('\n--- SAMPLES ---');
  console.log('Italy folder:');
  db.prepare("SELECT filename, country, city FROM photos WHERE file_path LIKE '%איטליה%' LIMIT 3")
    .all().forEach(p => console.log(`  ${p.filename}: ${p.country} / ${p.city}`));
  
  console.log('Slovenia folder:');
  db.prepare("SELECT filename, country, city FROM photos WHERE file_path LIKE '%סלובניה%' LIMIT 3")
    .all().forEach(p => console.log(`  ${p.filename}: ${p.country} / ${p.city}`));

  db.close();
}

main().catch(console.error);
