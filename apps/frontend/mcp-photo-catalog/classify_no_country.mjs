import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';

// Keywords en hebreo, español e inglés para detectar país
const COUNTRY_KEYWORDS = [
  // Israel
  { regex: /ישראל|israel/i, country: 'Israel' },
  { regex: /תל אביב|tel aviv/i, country: 'Israel', city: 'Tel Aviv' },
  { regex: /ירושלים|jerusalem/i, country: 'Israel', city: 'Jerusalem' },
  { regex: /חיפה|haifa/i, country: 'Israel', city: 'Haifa' },
  { regex: /אילת|eilat/i, country: 'Israel', city: 'Eilat' },
  
  // Italy
  { regex: /איטליה|italia|italy/i, country: 'Italy' },
  { regex: /פיזה|pisa/i, country: 'Italy', city: 'Pisa' },
  { regex: /רומא|roma|rome/i, country: 'Italy', city: 'Rome' },
  { regex: /ונציה|venecia|venice/i, country: 'Italy', city: 'Venice' },
  { regex: /פירנצה|florencia|florence/i, country: 'Italy', city: 'Florence' },
  { regex: /מילאנו|milan/i, country: 'Italy', city: 'Milan' },
  
  // Argentina
  { regex: /ארגנטינה|argentina/i, country: 'Argentina' },
  { regex: /ברילוצ'ה|bariloche/i, country: 'Argentina', city: 'Bariloche' },
  { regex: /מנדוזה|mendoza/i, country: 'Argentina', city: 'Mendoza' },
  { regex: /בואנוס איירס|buenos aires/i, country: 'Argentina', city: 'Buenos Aires' },
  { regex: /איגואסו|iguazu/i, country: 'Argentina', city: 'Iguazú' },
  
  // Slovenia
  { regex: /סלובניה|slovenia/i, country: 'Slovenia' },
  { regex: /לובליאנה|ljubljana/i, country: 'Slovenia', city: 'Ljubljana' },
  
  // Croatia
  { regex: /קרואטיה|croatia/i, country: 'Croatia' },
  { regex: /דוברובניק|dubrovnik/i, country: 'Croatia', city: 'Dubrovnik' },
  
  // Bosnia
  { regex: /בוסניה|bosnia/i, country: 'Bosnia and Herzegovina' },
  { regex: /סרajeבו|sarajevo/i, country: 'Bosnia and Herzegovina', city: 'Sarajevo' },
  
  // Greece
  { regex: /יוון|grecia|greece/i, country: 'Greece' },
  { regex: /כרתים|crete/i, country: 'Greece', city: 'Crete' },
  
  // Spain
  { regex: /ספרד|españa|spain/i, country: 'Spain' },
  
  // France
  { regex: /צרפת|francia|france/i, country: 'France' },
  
  // Denmark
  { regex: /דנמרק|denmark/i, country: 'Denmark' },
  { regex: /קופנהגן|copenhagen/i, country: 'Denmark', city: 'Copenhagen' },
  
  // Germany
  { regex: /גרמניה|alemania|germany/i, country: 'Germany' },
  
  // UK
  { regex: /אנגליה|england|uk/i, country: 'United Kingdom' },
  
  // USA
  { regex: /ארצות הברית|usa|eeuu/i, country: 'United States' },
  
  // Thailand
  { regex: /תאילנד|tailandia|thailand/i, country: 'Thailand' },
  
  // Japan
  { regex: /יפן|japon|japan/i, country: 'Japan' },
  
  // Morocco
  { regex: /מרוקו|marruecos|morocco/i, country: 'Morocco' },
  
  // Brazil
  { regex: /ברזיל|brasil|brazil/i, country: 'Brazil' },
  
  // Cyprus
  { regex: /קפריסין|cyprus/i, country: 'Cyprus' },
  
  // Montenegro
  { regex: /מונטנגרו|montenegro/i, country: 'Montenegro' },
];

// Known trips by date range
const KNOWN_TRIPS = [
  { country: 'Italy', start: '2023-10-03', end: '2023-10-11' },
  { country: 'Argentina', start: '2025-02-01', end: '2025-02-28' },
  { country: 'Argentina', start: '2011-11-07', end: '2012-02-06' },
  { country: 'Slovenia', start: '2015-08-01', end: '2015-08-15' },
  { country: 'Croatia', start: '2010-08-01', end: '2010-08-20' },
  { country: 'Greece', start: '2013-07-20', end: '2013-07-30' },
  { country: 'Bosnia and Herzegovina', start: '2023-09-01', end: '2023-09-10' },
  { country: 'Denmark', start: '2024-07-01', end: '2024-07-15' },
  { country: 'Cyprus', start: '2023-08-01', end: '2023-08-10' },
  { country: 'Montenegro', start: '2010-06-01', end: '2010-06-30' },
];

function getCountryFromPath(filePath) {
  for (const kw of COUNTRY_KEYWORDS) {
    if (kw.regex.test(filePath)) {
      return { country: kw.country, city: kw.city || null };
    }
  }
  return null;
}

function getCountryFromDate(dateTaken) {
  if (!dateTaken) return null;
  
  const dateStr = dateTaken.substring(0, 10); // YYYY-MM-DD
  
  for (const trip of KNOWN_TRIPS) {
    if (dateStr >= trip.start && dateStr <= trip.end) {
      return { country: trip.country, city: null };
    }
  }
  
  return null;
}

function getCountryFromFolder(folderPath, allPhotosMap) {
  // Check if sibling photos in same folder have country
  const siblings = allPhotosMap.get(folderPath);
  if (siblings && siblings.length > 0) {
    const withCountry = siblings.find(p => p.country && p.country !== '');
    if (withCountry) {
      return { country: withCountry.country, city: withCountry.city };
    }
  }
  return null;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  CLASIFICACIÓN DE FOTOS SIN COUNTRY');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);

  // Get all photos without country
  const noCountry = db.prepare("SELECT id, file_path, date_taken, country, city FROM photos WHERE country IS NULL OR country = ''").all();
  console.log('📊 Fotos sin country:', noCountry.length);

  // Build map of all photos by folder for sibling lookup
  const allPhotos = db.prepare('SELECT id, file_path, country, city FROM photos').all();
  const folderMap = new Map();
  for (const p of allPhotos) {
    const folder = path.dirname(p.file_path);
    if (!folderMap.has(folder)) folderMap.set(folder, []);
    folderMap.get(folder).push(p);
  }

  // Classify each photo
  let updated = 0;
  let byPath = 0;
  let byDate = 0;
  let byFolder = 0;
  let unclassified = 0;

  const updateStmt = db.prepare('UPDATE photos SET country = ?, city = COALESCE(?, city) WHERE id = ?');

  db.transaction(() => {
    for (const photo of noCountry) {
      let result = null;

      // Priority 1: Path keywords
      result = getCountryFromPath(photo.file_path);
      if (result) {
        updateStmt.run(result.country, result.city, photo.id);
        byPath++;
        updated++;
        continue;
      }

      // Priority 2: Known trips by date
      result = getCountryFromDate(photo.date_taken);
      if (result) {
        updateStmt.run(result.country, result.city, photo.id);
        byDate++;
        updated++;
        continue;
      }

      // Priority 3: Sibling photos in same folder
      const folder = path.dirname(photo.file_path);
      result = getCountryFromFolder(folder, folderMap);
      if (result) {
        updateStmt.run(result.country, result.city, photo.id);
        byFolder++;
        updated++;
        continue;
      }

      // Unclassified
      unclassified++;
    }
  })();

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  RESULTADOS');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`  📸 Total actualizadas: ${updated.toLocaleString()}`);
  console.log(`  📁 Por keywords en ruta: ${byPath.toLocaleString()}`);
  console.log(`  📅 Por KnownTrips: ${byDate.toLocaleString()}`);
  console.log(`  👥 Por carpeta hermana: ${byFolder.toLocaleString()}`);
  console.log(`  ❓ Sin clasificar: ${unclassified.toLocaleString()}`);

  // Final stats
  const totalWithCountry = db.prepare("SELECT COUNT(*) as c FROM photos WHERE country IS NOT NULL AND country != ''").get().c;
  const totalWithoutCountry = db.prepare("SELECT COUNT(*) as c FROM photos WHERE country IS NULL OR country = ''").get().c;
  
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  ESTADO FINAL');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`  Con country: ${totalWithCountry.toLocaleString()} (${((totalWithCountry / (totalWithCountry + totalWithoutCountry)) * 100).toFixed(1)}%)`);
  console.log(`  Sin country: ${totalWithoutCountry.toLocaleString()}`);

  // Country distribution
  const countries = db.prepare("SELECT country, COUNT(*) as c FROM photos WHERE country IS NOT NULL AND country != '' GROUP BY country ORDER BY c DESC").all();
  console.log('\n📊 Distribución por país:');
  countries.forEach(c => console.log(`  ${c.country}: ${c.c.toLocaleString()}`));

  db.close();
  console.log('\n✅ Clasificación completada.');
}

main().catch(console.error);
