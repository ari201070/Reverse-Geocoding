import Database from 'better-sqlite3';
import fs from 'fs';

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';

const PATH_KEYWORD_MAP = [
  { regex: /(פיזה|pisa)/i, city: 'Pisa', country: 'Italy' },
  { regex: /(רומא|roma|rome)/i, city: 'Rome', country: 'Italy' },
  { regex: /(ונציה|venecia|venice)/i, city: 'Venice', country: 'Italy' },
  { regex: /(פירנצה|florencia|florence)/i, city: 'Florence', country: 'Italy' },
  { regex: /(מילאנו|milan)/i, city: 'Milan', country: 'Italy' },
  { regex: /(נאפולי|napoli|naples)/i, city: 'Naples', country: 'Italy' },
  { regex: /(איטליה|italia|italy)/i, country: 'Italy' },
  { regex: /(ארגנטינה|argentina)/i, country: 'Argentina' },
  { regex: /(ברילוצ'ה|bariloche)/i, city: 'Bariloche', country: 'Argentina' },
  { regex: /(מנדוזה|mendoza)/i, city: 'Mendoza', country: 'Argentina' },
  { regex: /(איגואסו|iguazu|iguazú)/i, city: 'Iguazú', country: 'Argentina' },
  { regex: /(בואנוס איירס|buenos aires)/i, city: 'Buenos Aires', country: 'Argentina' },
  { regex: /(לאגו פואלו|lago puelo)/i, city: 'Lago Puelo', country: 'Argentina' },
  { regex: /(סאלטה|salta)/i, city: 'Salta', country: 'Argentina' },
  { regex: /(חוחוי|jujuy)/i, city: 'Jujuy', country: 'Argentina' },
  { regex: /(קורדובה|cordoba)/i, city: 'Córdoba', country: 'Argentina' },
  { regex: /(ספרד|españa|spain)/i, country: 'Spain' },
  { regex: /(צרפת|francia|france)/i, country: 'France' },
  { regex: /(גרמניה|alemania|germany)/i, country: 'Germany' },
  { regex: /(ברזיל|brasil|brazil)/i, country: 'Brazil' },
  { regex: /(אנגליה|england|uk)/i, country: 'United Kingdom' },
  { regex: /(ארצות הברית|usa|eeuu)/i, country: 'United States' },
  { regex: /(בוסניה|bosnia)/i, country: 'Bosnia and Herzegovina' },
  { regex: /(סרajeבו|sarajevo)/i, city: 'Sarajevo', country: 'Bosnia and Herzegovina' },
  { regex: /(יוון|grecia|greece)/i, country: 'Greece' },
  { regex: /(כרתים|crete)/i, city: 'Crete', country: 'Greece' },
  { regex: /(סלובניה|slovenia)/i, country: 'Slovenia' },
  { regex: /(לובליאנה|ljubljana)/i, city: 'Ljubljana', country: 'Slovenia' },
  { regex: /(קרואטיה|croatia)/i, country: 'Croatia' },
  { regex: /(דנמרק|denmark)/i, country: 'Denmark' },
  { regex: /(קופנהגן|copenhagen)/i, city: 'Copenhagen', country: 'Denmark' },
  { regex: /(תאילנד|tailandia|thailand)/i, country: 'Thailand' },
  { regex: /(יפן|japon|japan)/i, country: 'Japan' },
  { regex: /(מרוקו|marruecos|morocco)/i, country: 'Morocco' },
];

function ensureColumnsExist(db) {
  const columns = db.prepare("PRAGMA table_info(photos)").all().map(c => c.name);
  if (!columns.includes('country')) db.exec("ALTER TABLE photos ADD COLUMN country TEXT");
  if (!columns.includes('city')) db.exec("ALTER TABLE photos ADD COLUMN city TEXT");
}

function matchPathForKeywords(filePath) {
  for (const item of PATH_KEYWORD_MAP) {
    if (item.regex.test(filePath)) {
      return { country: item.country || null, city: item.city || null };
    }
  }
  return null;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  PROPAGACIÓN CONTEXTUAL MASIVA (OPTIMIZADA BATCH)');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);
  ensureColumnsExist(db);

  const totalPhotos = db.prepare("SELECT COUNT(*) as c FROM photos").get().c;
  const wrongCountry = db.prepare("SELECT COUNT(*) as c FROM photos WHERE country = 'Israel'").get().c;
  console.log(`📊 ESTADO INICIAL:`);
  console.log(`   Total fotos: ${totalPhotos.toLocaleString()}`);
  console.log(`   Con country='Israel': ${wrongCountry.toLocaleString()}\n`);

  // ═══════════════════════════════════════════════════════════════
  // CAPA 1: PATH KEYWORDS (BATCH)
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Capa 1: Inferencia Lingüística por Ruta...');
  
  const allPhotos = db.prepare("SELECT id, file_path, country, city FROM photos").all();
  const batchUpdates = [];

  for (const row of allPhotos) {
    if (!row.file_path) continue;
    const match = matchPathForKeywords(row.file_path);
    if (!match) continue;

    const shouldOverwriteCountry = match.country && (!row.country || row.country !== match.country);
    const shouldOverwriteCity = match.city && (!row.city || row.city !== match.city);

    if (shouldOverwriteCountry || shouldOverwriteCity) {
      batchUpdates.push({
        country: shouldOverwriteCountry ? match.country : null,
        city: shouldOverwriteCity ? match.city : null,
        id: row.id,
      });
    }
  }

  let capa1Updates = 0;
  if (batchUpdates.length > 0) {
    const updateStmt = db.prepare(`
      UPDATE photos SET 
        country = COALESCE(?, country),
        city = COALESCE(?, city)
      WHERE id = ?
    `);
    
    db.transaction(() => {
      for (const u of batchUpdates) {
        if (updateStmt.run(u.country, u.city, u.id).changes > 0) capa1Updates++;
      }
    })();
  }
  console.log(`   └─ ✅ ${capa1Updates.toLocaleString()} fotos actualizadas.\n`);

  // ═══════════════════════════════════════════════════════════════
  // CAPA 2: SISTER FOLDER (Group by exact folder path)
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Capa 2: Propagación por Carpeta Hermana...');
  
  // Extract full folder path (everything except the filename)
  const allWithFolders = db.prepare(`
    SELECT id, file_path, country, city,
           SUBSTR(file_path, 1, INSTR(file_path, '\\\\') - 1) as folder
    FROM photos WHERE file_path LIKE '%\\\\%'
  `).all();

  // Group by folder
  const folderMap = new Map();
  for (const row of allWithFolders) {
    if (!folderMap.has(row.folder)) folderMap.set(row.folder, []);
    folderMap.get(row.folder).push(row);
  }

  let capa2Updates = 0;
  const updateFolder = db.prepare(`UPDATE photos SET country = ?, city = ? WHERE id = ?`);

  db.transaction(() => {
    for (const [folder, photos] of folderMap) {
      // Find GPS-equipped photo with correct country in this exact folder
      const source = photos.find(p => 
        p.latitude && p.country && p.country !== '' && p.country !== 'Israel'
      );
      if (!source) continue;

      // Update all other photos in this folder
      for (const p of photos) {
        if (p.id === source.id) continue;
        if (!p.country || p.country === 'Israel' || p.country !== source.country) {
          updateFolder.run(source.country, source.city, p.id);
          capa2Updates++;
        }
      }
    }
  })();
  console.log(`   └─ ✅ ${capa2Updates.toLocaleString()} fotos heredaron de carpeta hermana.\n`);

  // ═══════════════════════════════════════════════════════════════
  // CAPA 3: KNOWN TRIPS (BATCH)
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Capa 3: Mapeo por KnownTrips...');
  
  const trips = [
    { country: 'Italy', start: '2023-10-03', end: '2023-10-11' },
    { country: 'Argentina', start: '2025-02-01', end: '2025-02-28' },
    { country: 'Argentina', start: '2011-11-07', end: '2012-02-06' },
    { country: 'Slovenia', start: '2015-08-01', end: '2015-08-15' },
    { country: 'Croatia', start: '2010-08-01', end: '2010-08-20' },
    { country: 'Greece', start: '2013-07-20', end: '2013-07-30' },
    { country: 'Bosnia and Herzegovina', start: '2023-09-01', end: '2023-09-10' },
    { country: 'Denmark', start: '2024-07-01', end: '2024-07-15' },
  ];

  let capa3Updates = 0;
  const updateTrip = db.prepare(`
    UPDATE photos SET country = ?
    WHERE DATE(date_taken) BETWEEN DATE(?) AND DATE(?)
      AND (country IS NULL OR country = '' OR country != ?)
  `);

  db.transaction(() => {
    for (const trip of trips) {
      capa3Updates += updateTrip.run(trip.country, trip.start, trip.end, trip.country).changes;
    }
  })();
  console.log(`   └─ ✅ ${capa3Updates.toLocaleString()} fotos mapeadas por KnownTrips.\n`);

  // ═══════════════════════════════════════════════════════════════
  // VALIDACIÓN FINAL
  // ═══════════════════════════════════════════════════════════════
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  VALIDACIÓN FINAL');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const stats = {
    total: db.prepare("SELECT COUNT(*) as c FROM photos").get().c,
    withCountry: db.prepare("SELECT COUNT(*) as c FROM photos WHERE country IS NOT NULL AND country != ''").get().c,
    withCity: db.prepare("SELECT COUNT(*) as c FROM photos WHERE city IS NOT NULL AND city != ''").get().c,
    stillIsrael: db.prepare("SELECT COUNT(*) as c FROM photos WHERE country = 'Israel'").get().c,
    noCountry: db.prepare("SELECT COUNT(*) as c FROM photos WHERE country IS NULL OR country = ''").get().c,
  };

  console.log(`📊 ESTADO FINAL:`);
  console.log(`   Total fotos: ${stats.total.toLocaleString()}`);
  console.log(`   Con country: ${stats.withCountry.toLocaleString()} (${((stats.withCountry/stats.total)*100).toFixed(1)}%)`);
  console.log(`   Con city: ${stats.withCity.toLocaleString()} (${((stats.withCity/stats.total)*100).toFixed(1)}%)`);
  console.log(`   Todavía Israel: ${stats.stillIsrael.toLocaleString()}`);
  console.log(`   Sin country: ${stats.noCountry.toLocaleString()}\n`);

  // Muestra
  console.log('🔍 MUESTRA (carpeta איטליה):');
  db.prepare("SELECT filename, country, city FROM photos WHERE file_path LIKE '%איטליה%' LIMIT 5")
    .all().forEach(p => console.log(`   ${p.filename}: ${p.country} / ${p.city}`));

  console.log('\n🔍 MUESTRA (carpeta גברים רעבים באיטליה):');
  db.prepare("SELECT filename, country, city FROM photos WHERE file_path LIKE '%גברים רעבים באיטליה%' LIMIT 5")
    .all().forEach(p => console.log(`   ${p.filename}: ${p.country} / ${p.city}`));

  console.log('\n🔍 MUESTRA (carpeta סלובניה):');
  db.prepare("SELECT filename, country, city FROM photos WHERE file_path LIKE '%סלובניה%' LIMIT 5")
    .all().forEach(p => console.log(`   ${p.filename}: ${p.country} / ${p.city}`));

  db.close();
  console.log('\n✅ Propagación completada.');
}

main().catch(console.error);
