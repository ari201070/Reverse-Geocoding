#!/usr/bin/env node
/**
 * run-import-pipeline.mjs
 * 
 * Entry point que enlaza todos los servicios modulares:
 *   TripAggregator → TripExporter → JSON files para localStorage
 * 
 * Uso: node run-import-pipeline.mjs [--min-year=2002] [--max-year=2030]
 * 
 * Salida en photo-import-output/:
 *   - photo-trips-{timestamp}.json           → Revisión completa (trips + activities + stats)
 *   - travel_trips_import_{timestamp}.json    → Para localStorage "travel_trips"
 *   - travel_bookings_import_{timestamp}.json → Para localStorage "travel_bookings"
 *   - trip-summary-{timestamp}.txt           → Resumen legible
 */

import { TripAggregator } from './src/services/TripAggregator.js';
import { TripExporter } from './src/services/TripExporter.js';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = path.join(__dirname, '..', 'photo-import-output');

// Parse CLI args
const args = Object.fromEntries(
  process.argv.slice(2).map(a => {
    const [k, v] = a.replace(/^--/, '').split('=');
    return [k, v];
  })
);

const minYear = parseInt(args['min-year'] || '2002');
const maxYear = parseInt(args['max-year'] || '2030');

async function main() {
  console.error('═══════════════════════════════════════════════');
  console.error('  PHOTO IMPORT PIPELINE - Versión Modular');
  console.error('═══════════════════════════════════════════════');
  console.error(`  Rango de años: ${minYear} - ${maxYear}`);
  console.error('═══════════════════════════════════════════════\n');

  // 1. Ejecutar agregación
  const aggregator = new TripAggregator({
    minYear,
    maxYear,
  });

  const result = await aggregator.process({ minYear, maxYear });

  // 2. Exportar con TripExporter
  const exporter = new TripExporter(OUTPUT_DIR);
  const outputFiles = exporter.export(result);

  // 3. Generar travel_trips_import.json en formato compatible con la app
  const tripsForStorage = result.trips
    .filter(t => t.source === 'booking_document') // Solo viajes reales
    .map(t => ({
      id: t.id,
      name: t.name,
      destination: t.cities?.[0] || t.country || '',
      startDate: t.startDate,
      endDate: t.endDate,
      color: t.color || 'indigo',
    }));

  const tripsPath = path.join(OUTPUT_DIR, `travel_trips_import_${Date.now()}.json`);
  fs.writeFileSync(tripsPath, JSON.stringify(tripsForStorage, null, 2));

  // 4. Resumen final en consola
  console.log('\n═══════════════════════════════════════════════');
  console.log('  📊 RESUMEN DEL PIPELINE');
  console.log('═══════════════════════════════════════════════');
  console.log(`  📸 Total fotos procesadas: ${result.stats.totalPhotos}`);
  console.log(`  🗺️  Fotos enriquecidas (H3): ${result.stats.enrichedPhotos}`);
  console.log(`  📄 Viajes desde documentos: ${result.stats.knownTrips}`);
  console.log(`  🌍 Viajes internacionales: ${result.stats.internationalTrips}`);
  console.log(`  🏠 Actividades locales: ${result.stats.localTrips}`);
  console.log(`  🎯 Actividades generadas: ${result.stats.activities}`);
  console.log(`  ❓ Fotos no asignadas: ${result.stats.unassigned}`);
  console.log('───────────────────────────────────────────────');
  console.log('  📂 ARCHIVOS GENERADOS:');
  console.log(`     📋 Revisión completa:      ${outputFiles.tripsFile}`);
  console.log(`     🏠 Trips para app:         ${tripsPath}`);
  console.log(`     📦 Bookings para app:      ${outputFiles.bookingsFile}`);
  console.log(`     📝 Resumen legible:        ${outputFiles.summaryFile}`);
  console.log('═══════════════════════════════════════════════');

  // 5. Detalle por viaje
  console.log('\n  🌍 VIAJES DETECTADOS:');
  for (const trip of result.trips.filter(t => t.source === 'booking_document')) {
    const tripActivities = result.activities.filter(a => a.tripId === trip.id);
    console.log(`\n  ✈️  ${trip.name}`);
    console.log(`     📅 ${trip.startDate} → ${trip.endDate}`);
    console.log(`     🏳️  ${trip.countries?.join(', ') || trip.country}`);
    console.log(`     📷 ${trip.totalPhotos} fotos | ${tripActivities.length} actividades`);
  }

  // 6. Instrucciones de importación
  console.log('\n═══════════════════════════════════════════════');
  console.log('  📥 CÓMO IMPORTAR EN LA APP');
  console.log('═══════════════════════════════════════════════');
  console.log('  1. Abre la app en el navegador');
  console.log('  2. Abre DevTools (F12) → Console');
  console.log('  3. Ejecuta:');
  console.log('');
  console.log(`     // Trips`);
  console.log(`     localStorage.setItem("travel_trips", \`$(cat "${tripsPath.replace(/\\/g, '\\\\')}")\`);`);
  console.log('');
  console.log(`     // Bookings`);
  console.log(`     localStorage.setItem("travel_bookings", \`$(cat "${outputFiles.bookingsFile.replace(/\\/g, '\\\\')}")\`);`);
  console.log('');
  console.log('  4. Recarga la página');
  console.log('  ↩️  Para revertir: localStorage.removeItem("travel_trips")');
  console.log('                   localStorage.removeItem("travel_bookings")');
  console.log('═══════════════════════════════════════════════\n');
}

main().catch(err => {
  console.error('❌ Error en el pipeline:', err);
  process.exit(1);
});
