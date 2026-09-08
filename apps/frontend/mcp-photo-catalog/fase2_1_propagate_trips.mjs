/**
 * Fase 2.1: Propagación contextual de trip_name por carpeta hermana
 * 
 * REGLAS:
 * - Sin llamadas a APIs externas
 * - Solo propagación por carpeta compartida
 * - NO mover archivos físicos
 * - Generar resumen_fase2_1.json
 */

import Database from 'better-sqlite3';
import fs from 'fs';

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const OUTPUT_PATH = './resumen_fase2_1.json';

// Viajes conocidos (mismo KnownTrips.js)
const KNOWN_TRIPS = {
  'argentina-2011': { name: 'Argentina 2011-2012', country: 'Argentina' },
  'argentina-2025': { name: 'Argentina 2025', country: 'Argentina' },
  'slovenia-2015': { name: 'Eslovenia 2015', country: 'Slovenia' },
  'italy-2023': { name: 'Italia 2023', country: 'Italy' },
  'bosnia-2023': { name: 'Bosnia 2023', country: 'Bosnia and Herzegovina' },
  'denmark-2024': { name: 'Dinamarca 2024', country: 'Denmark' },
  'crete-2013': { name: 'Creta 2013', country: 'Crete' },
  'croatia-montenegro-2010': { name: 'Croacia+Montenegro 2010', country: 'Croatia' },
};

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 2.1: PROPAGACIÓN CONTEXTUAL DE TRIPS');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);

  // 1. Cargar mapping de Phase 1
  const tripMappingPath = './trip_mapping.json';
  let tripMapping = {};
  if (fs.existsSync(tripMappingPath)) {
    tripMapping = JSON.parse(fs.readFileSync(tripMappingPath, 'utf8'));
    console.log(`📋 Trip mapping cargado: ${Object.keys(tripMapping).length} fotos con trip asignado`);
  } else {
    console.log('⚠️ No se encontró trip_mapping.json');
  }

  // 2. Aplicar trip_mapping a la DB
  console.log('\n🔹 Paso 0: Aplicando trip_mapping de Phase 1...');
  
  let appliedCount = 0;
  const applyStmt = db.prepare("UPDATE photos SET trip_name = ? WHERE id = ?");
  
  db.transaction(() => {
    for (const [photoId, tripId] of Object.entries(tripMapping)) {
      applyStmt.run(tripId, parseInt(photoId));
      appliedCount++;
    }
  })();
  
  console.log(`   └─ ✅ ${appliedCount.toLocaleString()} trip_names aplicados desde Phase 1.\n`);

  // 3. Estado inicial
  const totalPhotos = db.prepare("SELECT COUNT(*) as c FROM photos").get().c;
  const withTrip = db.prepare("SELECT COUNT(*) as c FROM photos WHERE trip_name IS NOT NULL AND trip_name != ''").get().c;
  const withoutTrip = totalPhotos - withTrip;
  
  console.log(`📊 ESTADO INICIAL:`);
  console.log(`   Total fotos: ${totalPhotos.toLocaleString()}`);
  console.log(`   Con trip_name: ${withTrip.toLocaleString()}`);
  console.log(`   Sin trip_name: ${withoutTrip.toLocaleString()}\n`);

  // 2. Obtener todas las fotos con su folder path
  console.log('🔹 Paso 1: Extrayendo rutas de carpetas...');
  
  const allPhotos = db.prepare(`
    SELECT id, file_path, trip_name, country, city
    FROM photos WHERE file_path IS NOT NULL
  `).all();

  // Extract folder path in JavaScript (more reliable than SQLite string functions)
  for (const photo of allPhotos) {
    const pathParts = photo.file_path.split('\\');
    if (pathParts.length > 1) {
      photo.folder = pathParts.slice(0, -1).join('\\');
    } else {
      photo.folder = null;
    }
  }

  // 4. Agrupar por carpeta
  const folderMap = new Map();
  for (const row of allPhotos) {
    if (!row.folder) continue;
    if (!folderMap.has(row.folder)) folderMap.set(row.folder, []);
    folderMap.get(row.folder).push(row);
  }

  console.log(`   └─ ${folderMap.size.toLocaleString()} carpetas encontradas.\n`);

  // 4. Propagar trip_name por carpeta hermana
  console.log('🔹 Paso 2: Propagación por carpeta hermana...');
  
  let propagatedCount = 0;
  let propagatedDetails = [];
  
  const updateStmt = db.prepare(`
    UPDATE photos SET trip_name = ?, country = COALESCE(country, ?), city = COALESCE(city, ?)
    WHERE id = ?
  `);

  db.transaction(() => {
    for (const [folder, photos] of folderMap) {
      // Buscar foto con trip_name en esta carpeta
      const source = photos.find(p => p.trip_name && p.trip_name !== '');
      if (!source) continue;
      
      const tripInfo = KNOWN_TRIPS[source.trip_name];
      if (!tripInfo) continue;

      // Propagar a otras fotos en la misma carpeta
      for (const p of photos) {
        if (p.id === source.id) continue;
        if (p.trip_name && p.trip_name !== '') continue; // Ya tiene trip
        
        updateStmt.run(source.trip_name, tripInfo.country, null, p.id);
        propagatedCount++;
        
        propagatedDetails.push({
          photo_id: p.id,
          filename: p.filename,
          from_folder: folder,
          propagated_trip: source.trip_name,
          propagated_country: tripInfo.country,
        });
      }
    }
  })();

  console.log(`   └─ ✅ ${propagatedCount.toLocaleString()} fotos recibieron trip_name por herencia.\n`);

  // 5. Estado final
  const finalWithTrip = db.prepare("SELECT COUNT(*) as c FROM photos WHERE trip_name IS NOT NULL AND trip_name != ''").get().c;
  const finalWithoutTrip = totalPhotos - finalWithTrip;
  
  console.log(`📊 ESTADO FINAL:`);
  console.log(`   Con trip_name: ${finalWithTrip.toLocaleString()} (+${propagatedCount.toLocaleString()})`);
  console.log(`   Sin trip_name: ${finalWithoutTrip.toLocaleString()}\n`);

  // 6. Distribución por trip
  console.log('🔹 Distribución por viaje:');
  const tripDist = db.prepare(`
    SELECT trip_name, COUNT(*) as cnt 
    FROM photos 
    WHERE trip_name IS NOT NULL AND trip_name != ''
    GROUP BY trip_name 
    ORDER BY cnt DESC
  `).all();
  
  tripDist.forEach(t => console.log(`   ${t.trip_name}: ${t.cnt.toLocaleString()}`));

  // 7. Guardar estadísticas
  const stats = {
    total: totalPhotos,
    initial_with_trip: withTrip,
    initial_without_trip: withoutTrip,
    propagated: propagatedCount,
    final_with_trip: finalWithTrip,
    final_without_trip: finalWithoutTrip,
    trip_distribution: tripDist,
    propagation_details: propagatedDetails.slice(0, 100), // Primeros 100 para referencia
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(stats, null, 2));
  console.log(`\n✅ Resumen guardado en: ${OUTPUT_PATH}`);

  db.close();
}

main().catch(console.error);
