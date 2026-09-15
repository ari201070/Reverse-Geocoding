/**
 * Fase 3: Propagación por Carpetas Hermanas y Ventanas Temporales
 * 
 * REGLAS:
 * - Propagar trip_name, country, city por carpeta compartida
 * - Propagar trip_name y country por rango de fechas
 * - NO sobreescribir campos con valores existentes
 * - Generar resumen_fase3.json
 */

import Database from 'better-sqlite3';
import fs from 'fs';

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const OUTPUT_PATH = './resumen_fase3.json';

// Viajes conocidos con rangos de fechas
const KNOWN_TRIPS = [
  { id: 'argentina-2011', name: 'Argentina 2011-2012', country: 'Argentina', startDate: '2011-11-07', endDate: '2012-02-06' },
  { id: 'slovenia-2015', name: 'Eslovenia 2015', country: 'Slovenia', startDate: '2015-07-02', endDate: '2015-07-06' },
  { id: 'croatia-montenegro-2010', name: 'Croacia+Montenegro 2010', country: 'Croatia', startDate: '2010-06-24', endDate: '2010-06-30' },
  { id: 'crete-2013', name: 'Creta 2013', country: 'Crete', startDate: '2013-07-23', endDate: '2013-07-27' },
  { id: 'italy-2023', name: 'Italia 2023', country: 'Italy', startDate: '2023-10-03', endDate: '2023-10-11' },
  { id: 'bosnia-2023', name: 'Bosnia 2023', country: 'Bosnia and Herzegovina', startDate: '2023-05-01', endDate: '2023-05-05' },
  { id: 'argentina-2025', name: 'Argentina 2025', country: 'Argentina', startDate: '2025-09-26', endDate: '2025-10-30' },
  { id: 'denmark-2024', name: 'Dinamarca 2024', country: 'Denmark', startDate: '2024-09-15', endDate: '2024-09-20' },
];

function extractFolder(filePath) {
  if (!filePath) return null;
  const parts = filePath.split('\\');
  return parts.length > 1 ? parts.slice(0, -1).join('\\') : null;
}

function findTripByDate(dateStr) {
  if (!dateStr) return null;
  const date = dateStr.split(' ')[0]; // Extract YYYY-MM-DD
  for (const trip of KNOWN_TRIPS) {
    if (date >= trip.startDate && date <= trip.endDate) {
      return trip;
    }
  }
  return null;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 3: PROPAGACIÓN POR CARPETAS Y FECHAS');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);
  
  // SQLite optimizations
  db.pragma('journal_mode = WAL');
  db.pragma('busy_timeout = 5000');
  console.log('✅ SQLite WAL mode + busy_timeout activados\n');

  // Estado inicial
  const totalBefore = db.prepare('SELECT COUNT(*) as cnt FROM photos').get().cnt;
  const withTripBefore = db.prepare("SELECT COUNT(*) as cnt FROM photos WHERE trip_name IS NOT NULL AND trip_name != ''").get().cnt;
  console.log(`📊 ESTADO INICIAL:`);
  console.log(`   Total fotos: ${totalBefore.toLocaleString()}`);
  console.log(`   Con trip_name: ${withTripBefore.toLocaleString()} (${((withTripBefore/totalBefore)*100).toFixed(1)}%)\n`);

  // ═══════════════════════════════════════════════════════════════
  // CAPA 1: PROPAGACIÓN POR CARPETA HERMANA
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Capa 1: Propagación por Carpeta Hermana...');

  const allPhotos = db.prepare(`
    SELECT id, file_path, trip_name, country, city, date_taken
    FROM photos WHERE file_path IS NOT NULL
  `).all();

  // Extract folder for each photo
  for (const photo of allPhotos) {
    photo.folder = extractFolder(photo.file_path);
  }

  // Group by folder
  const folderMap = new Map();
  for (const photo of allPhotos) {
    if (!photo.folder) continue;
    if (!folderMap.has(photo.folder)) folderMap.set(photo.folder, []);
    folderMap.get(photo.folder).push(photo);
  }

  let folderUpdates = 0;
  const updateFolder = db.prepare(`
    UPDATE photos SET 
      trip_name = CASE WHEN trip_name IS NULL OR trip_name = '' THEN ? ELSE trip_name END,
      country = CASE WHEN country IS NULL OR country = '' THEN ? ELSE country END,
      city = CASE WHEN city IS NULL OR city = '' THEN ? ELSE city END
    WHERE id = ?
  `);

  db.transaction(() => {
    for (const [folder, photos] of folderMap) {
      // Find source photo with most metadata
      const source = photos.find(p => p.trip_name && p.country);
      if (!source) continue;

      // Propagate to other photos in same folder
      for (const p of photos) {
        if (p.id === source.id) continue;
        if (p.trip_name && p.country) continue; // Already has metadata

        const changes = updateFolder.run(
          source.trip_name || null,
          source.country || null,
          source.city || null,
          p.id
        );
        if (changes.changes > 0) folderUpdates++;
      }
    }
  })();

  console.log(`   └─ ✅ ${folderUpdates.toLocaleString()} fotos actualizadas por carpeta hermana.\n`);

  // ═══════════════════════════════════════════════════════════════
  // CAPA 2: PROPAGACIÓN POR VENTANA TEMPORAL
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Capa 2: Propagación por Ventana Temporal...');

  const photosWithoutTrip = db.prepare(`
    SELECT id, date_taken, trip_name, country
    FROM photos 
    WHERE (trip_name IS NULL OR trip_name = '')
      AND date_taken IS NOT NULL
  `).all();

  let temporalUpdates = 0;
  const updateTemporal = db.prepare(`
    UPDATE photos SET 
      trip_name = CASE WHEN trip_name IS NULL OR trip_name = '' THEN ? ELSE trip_name END,
      country = CASE WHEN country IS NULL OR country = '' THEN ? ELSE country END
    WHERE id = ?
  `);

  db.transaction(() => {
    for (const photo of photosWithoutTrip) {
      const trip = findTripByDate(photo.date_taken);
      if (trip) {
        const changes = updateTemporal.run(trip.id, trip.country, photo.id);
        if (changes.changes > 0) temporalUpdates++;
      }
    }
  })();

  console.log(`   └─ ✅ ${temporalUpdates.toLocaleString()} fotos actualizadas por fecha.\n`);

  // ═══════════════════════════════════════════════════════════════
  // REPORTE FINAL
  // ═══════════════════════════════════════════════════════════════
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  REPORTE FINAL - FASE 3');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const totalAfter = db.prepare('SELECT COUNT(*) as cnt FROM photos').get().cnt;
  const withTripAfter = db.prepare("SELECT COUNT(*) as cnt FROM photos WHERE trip_name IS NOT NULL AND trip_name != ''").get().cnt;

  console.log(`📊 ESTADO FINAL:`);
  console.log(`   Total fotos: ${totalAfter.toLocaleString()}`);
  console.log(`   Con trip_name: ${withTripAfter.toLocaleString()} (${((withTripAfter/totalAfter)*100).toFixed(1)}%)`);
  console.log(`   Incremento: +${(withTripAfter - withTripBefore).toLocaleString()} fotos\n`);

  // Distribución por viaje
  console.log('🔹 Distribución por viaje:');
  const tripDist = db.prepare(`
    SELECT trip_name, COUNT(*) as cnt 
    FROM photos 
    WHERE trip_name IS NOT NULL AND trip_name != ''
    GROUP BY trip_name 
    ORDER BY cnt DESC
  `).all();
  tripDist.forEach(t => console.log(`   ${t.trip_name}: ${t.cnt.toLocaleString()}`));

  // Fotos sin trip restantes
  const noTripRemaining = db.prepare(`
    SELECT country, COUNT(*) as cnt 
    FROM photos 
    WHERE (trip_name IS NULL OR trip_name = '')
    GROUP BY country 
    ORDER BY cnt DESC
  `).all();

  console.log('\n🔹 Fotos sin trip por país:');
  noTripRemaining.forEach(c => console.log(`   ${c.country || 'NULL'}: ${c.cnt.toLocaleString()}`));

  // Guardar resumen
  const stats = {
    folder_updates: folderUpdates,
    temporal_updates: temporalUpdates,
    total_before: totalBefore,
    with_trip_before: withTripBefore,
    total_after: totalAfter,
    with_trip_after: withTripAfter,
    trip_distribution: tripDist,
    no_trip_by_country: noTripRemaining,
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(stats, null, 2));
  console.log(`\n✅ Resumen guardado en: ${OUTPUT_PATH}`);

  db.close();
}

main().catch(console.error);
