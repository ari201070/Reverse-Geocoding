/**
 * Fase 3.5: Enriquecimiento Fino por País, Patrones y QA
 * 
 * REGLAS:
 * - Argentina 2025: Solo Sept/Oct 2025
 * - Dinamarca: Diferenciar 2020 vs 2024
 * - Rescate Argentina 2011: Patrones de nombre y carpeta
 * - Asignación directa por país
 * - QA: Detectar incoherencias
 */

import Database from 'better-sqlite3';
import fs from 'fs';

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const OUTPUT_PATH = './resumen_fase3_5.json';

// Keywords for Argentina 2011 rescue
const ARGENTINA_2011_KEYWORDS = [
  'Lago Puelo', 'לאגו פואלו', 'Glaciar', 'Perito Moreno', 
  'Gobernador Costa', 'Chalten', 'צ\'לטאן', 'Calafate', 
  'Bariloche', 'Patagonia', 'טיול', 'ארגנטינה'
];

const HEBREW_ARGENTINA_FOLDER = 'טיול לארגנטינה';
const NOVIEMBRE_2011_PATH = 'F:\\2011\\Noviembre';

function extractYear(dateStr) {
  if (!dateStr) return null;
  const match = dateStr.match(/^(\d{4})/);
  return match ? parseInt(match[1]) : null;
}

function extractMonth(dateStr) {
  if (!dateStr) return null;
  const match = dateStr.match(/^\d{4}-(\d{2})/);
  return match ? parseInt(match[1]) : null;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  FASE 3.5: ENRIQUECIMIENTO FINO + QA');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');
  db.pragma('busy_timeout = 5000');

  const stats = {
    argentina_2025: 0,
    denmark_2020: 0,
    denmark_2024: 0,
    argentina_2011_rescue: 0,
    italy_direct: 0,
    greece_direct: 0,
    cyprus_direct: 0,
    slovenia_direct: 0,
    balkans_direct: 0,
    qa_incoherencias: 0,
  };

  // ═══════════════════════════════════════════════════════════════
  // REGLA 1: Argentina 2025 (Solo Sept/Oct 2025)
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Regla 1: Argentina 2025 (Sept/Oct 2025)...');
  
  const arg2025 = db.prepare(`
    UPDATE photos SET trip_name = 'argentina-2025'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country = 'Argentina'
      AND (
        (strftime('%Y-%m', date_taken) = '2025-09') OR
        (strftime('%Y-%m', date_taken) = '2025-10')
      )
  `).run();
  
  stats.argentina_2025 = arg2025.changes;
  console.log(`   └─ ✅ ${stats.argentina_2025} fotos asignadas a Argentina 2025.\n`);

  // ═══════════════════════════════════════════════════════════════
  // REGLA 2: Dinamarca (Diferenciar 2020 vs 2024)
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Regla 2: Dinamarca (2020 vs 2024)...');
  
  const dk2020 = db.prepare(`
    UPDATE photos SET trip_name = 'denmark-2020'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country IN ('Denmark', 'Dinamarca')
      AND strftime('%Y', date_taken) = '2020'
  `).run();
  
  const dk2024 = db.prepare(`
    UPDATE photos SET trip_name = 'denmark-2024'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country IN ('Denmark', 'Dinamarca')
      AND strftime('%Y', date_taken) = '2024'
  `).run();
  
  stats.denmark_2020 = dk2020.changes;
  stats.denmark_2024 = dk2024.changes;
  console.log(`   └─ ✅ Dinamarca 2020: ${stats.denmark_2020} | Dinamarca 2024: ${stats.denmark_2024}\n`);

  // ═══════════════════════════════════════════════════════════════
  // REGLA 3: Rescate Argentina 2011 (Patrones de nombre/carpeta)
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Regla 3: Rescate Argentina 2011...');
  
  // Get all photos without trip in Argentina or with Hebrew Argentina folder
  const argCandidates = db.prepare(`
    SELECT id, file_path, filename, country, trip_name
    FROM photos 
    WHERE (trip_name IS NULL OR trip_name = '')
      AND (
        country = 'Argentina' OR
        file_path LIKE '%טיול לארגנטינה%' OR
        file_path LIKE '%${NOVIEMBRE_2011_PATH}%'
      )
  `).all();

  let rescueCount = 0;
  const updateRescue = db.prepare(`
    UPDATE photos SET trip_name = 'argentina-2011', country = 'Argentina'
    WHERE id = ?
  `);

  db.transaction(() => {
    for (const photo of argCandidates) {
      const pathLower = (photo.file_path || '').toLowerCase();
      const filenameLower = (photo.filename || '').toLowerCase();
      
      // Check if in Noviembre 2011 folder
      const inNoviembre2011 = photo.file_path && photo.file_path.includes('2011\\Noviembre');
      const inHebrewFolder = photo.file_path && photo.file_path.includes(HEBREW_ARGENTINA_FOLDER);
      
      // Check for keywords
      const hasKeyword = ARGENTINA_2011_KEYWORDS.some(kw => 
        pathLower.includes(kw.toLowerCase()) || filenameLower.includes(kw.toLowerCase())
      );
      
      if (inNoviembre2011 || inHebrewFolder || hasKeyword) {
        updateRescue.run(photo.id);
        rescueCount++;
      }
    }
  })();
  
  stats.argentina_2011_rescue = rescueCount;
  console.log(`   └─ ✅ ${stats.argentina_2011_rescue} fotos rescatadas para Argentina 2011.\n`);

  // ═══════════════════════════════════════════════════════════════
  // REGLA 4: Asignación Directa por País
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 Regla 4: Asignación directa por país...');
  
  // Italy
  const italy = db.prepare(`
    UPDATE photos SET trip_name = 'italy-2023'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country IN ('Italy', 'Italia')
  `).run();
  stats.italy_direct = italy.changes;
  
  // Greece/Crete
  const greece = db.prepare(`
    UPDATE photos SET trip_name = 'crete-2013'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country IN ('Greece', 'Grecia')
  `).run();
  stats.greece_direct = greece.changes;
  
  // Cyprus
  const cyprus = db.prepare(`
    UPDATE photos SET trip_name = 'cyprus'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country IN ('Cyprus', 'Chipre')
  `).run();
  stats.cyprus_direct = cyprus.changes;
  
  // Slovenia
  const slovenia = db.prepare(`
    UPDATE photos SET trip_name = 'slovenia-2015'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country IN ('Slovenia', 'Eslovenia')
  `).run();
  stats.slovenia_direct = slovenia.changes;
  
  // Balkans (Croatia, Montenegro, Bosnia)
  const croatia2010 = db.prepare(`
    UPDATE photos SET trip_name = 'croatia-montenegro-2010'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country IN ('Croatia', 'Montenegro')
      AND strftime('%Y', date_taken) = '2010'
  `).run();
  
  const bosnia2023 = db.prepare(`
    UPDATE photos SET trip_name = 'bosnia-2023'
    WHERE (trip_name IS NULL OR trip_name = '')
      AND country = 'Bosnia and Herzegovina'
      AND strftime('%Y', date_taken) = '2023'
  `).run();
  
  stats.balkans_direct = croatia2010.changes + bosnia2023.changes;
  
  console.log(`   └─ ✅ Italia: ${stats.italy_direct} | Creta: ${stats.greece_direct}`);
  console.log(`   └─ ✅ Chipre: ${stats.cyprus_direct} | Eslovenia: ${stats.slovenia_direct}`);
  console.log(`   └─ ✅ Balcanes: ${stats.balkans_direct}\n`);

  // ═══════════════════════════════════════════════════════════════
  // QA: DETECCIÓN DE INCOHERENCIAS
  // ═══════════════════════════════════════════════════════════════
  console.log('🔹 QA: Detectando incoherencias...');
  
  // Check for international trips with Israel country
  const incoherencias = db.prepare(`
    SELECT id, filename, country, trip_name, file_path
    FROM photos
    WHERE country = 'Israel'
      AND trip_name IS NOT NULL
      AND trip_name != ''
      AND trip_name NOT LIKE '%israel%'
  `).all();
  
  stats.qa_incoherencias = incoherencias.length;
  
  if (incoherencias.length > 0) {
    console.log(`   ⚠️ ALERTA: ${incoherencias.length} fotos con country=Israel pero trip internacional`);
    incoherencias.slice(0, 5).forEach(inc => {
      console.log(`      - ${inc.filename}: trip=${inc.trip_name}`);
    });
    
    // Fix: Reset trip_name for these photos
    const fixIncoherencias = db.prepare(`
      UPDATE photos SET trip_name = NULL
      WHERE country = 'Israel'
        AND trip_name IS NOT NULL
        AND trip_name != ''
        AND trip_name NOT LIKE '%israel%'
    `).run();
    
    console.log(`   └─ ✅ ${fixIncoherencias.changes} incoherencias corregidas`);
  } else {
    console.log(`   └─ ✅ No se encontraron incoherencias`);
  }

  // ═══════════════════════════════════════════════════════════════
  // REPORTE FINAL
  // ═══════════════════════════════════════════════════════════════
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  REPORTE FINAL - FASE 3.5');
  console.log('═══════════════════════════════════════════════════════════════\n');

  // Final stats
  const totalAfter = db.prepare('SELECT COUNT(*) as cnt FROM photos').get().cnt;
  const withTripAfter = db.prepare("SELECT COUNT(*) as cnt FROM photos WHERE trip_name IS NOT NULL AND trip_name != ''").get().cnt;
  const localPhotos = db.prepare("SELECT COUNT(*) as cnt FROM photos WHERE country = 'Israel'").get().cnt;

  console.log('📊 RESUMEN DE CAMBIOS:');
  console.log(`   Argentina 2025 (Sept/Oct): ${stats.argentina_2025}`);
  console.log(`   Dinamarca 2020: ${stats.denmark_2020}`);
  console.log(`   Dinamarca 2024: ${stats.denmark_2024}`);
  console.log(`   Argentina 2011 (rescatadas): ${stats.argentina_2011_rescue}`);
  console.log(`   Italia (directo): ${stats.italy_direct}`);
  console.log(`   Creta (directo): ${stats.greece_direct}`);
  console.log(`   Chipre (directo): ${stats.cyprus_direct}`);
  console.log(`   Eslovenia (directo): ${stats.slovenia_direct}`);
  console.log(`   Balcanes (directo): ${stats.balkans_direct}`);
  console.log(`   Incoherencias corregidas: ${stats.qa_incoherencias}\n`);

  console.log('📊 ESTADO FINAL:');
  console.log(`   Total fotos: ${totalAfter.toLocaleString()}`);
  console.log(`   Con trip_name: ${withTripAfter.toLocaleString()} (${((withTripAfter/totalAfter)*100).toFixed(1)}%)`);
  console.log(`   Fotos locales (Israel): ${localPhotos.toLocaleString()}`);
  console.log(`   Fotos internacionales restantes: ${(totalAfter - withTripAfter - localPhotos).toLocaleString()}\n`);

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

  // Guardar resumen
  stats.total_after = totalAfter;
  stats.with_trip_after = withTripAfter;
  stats.local_photos = localPhotos;
  stats.trip_distribution = tripDist;
  
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(stats, null, 2));
  console.log(`\n✅ Resumen guardado en: ${OUTPUT_PATH}`);

  db.close();
}

main().catch(console.error);
