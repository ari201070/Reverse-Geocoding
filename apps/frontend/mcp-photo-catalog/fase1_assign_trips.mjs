/**
 * Fase 1: Asignación determinística de trips usando KnownTrips.js + timestamps
 * 
 * REGLAS:
 * - Sin llamadas a APIs externas
 * - Solo cruce DB ↔ KnownTrips.js
 * - NO mover archivos físicos
 * - Generar resumen_fase1.json
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

// Viajes conocidos (mismo KnownTrips.js)
const KNOWN_TRIPS = [
  {
    id: 'argentina-2011',
    name: 'Argentina 2011-2012',
    country: 'Argentina',
    cities: ['Buenos Aires', 'Calafate', 'Trevelin', 'Los Antiguos', 'Glaciar Perito Moreno', 'Caleta Valdés', 'Puerto Pirámides'],
    startDate: '2011-11-07',
    endDate: '2012-02-06',
  },
  {
    id: 'slovenia-2015',
    name: 'Eslovenia 2015',
    country: 'Slovenia',
    cities: ['Bled', 'Podhom', 'Ribčev Laz', 'Ukanc', 'Bohinjska Bistrica', 'Stara Fužina', 'Bohinjska Bela'],
    startDate: '2015-07-02',
    endDate: '2015-07-06',
  },
  {
    id: 'croatia-montenegro-2010',
    name: 'Croacia+Montenegro 2010',
    country: 'Croatia',
    countries: ['Croatia', 'Montenegro'],
    cities: ['Dubrovnik', 'Podgorica', 'Kolašin', 'Budva', 'Velji Bostur', 'Kotor', 'Škaljari'],
    startDate: '2010-06-24',
    endDate: '2010-06-30',
  },
  {
    id: 'crete-2013',
    name: 'Creta 2013',
    country: 'Crete',
    countries: ['Crete', 'Greece'],
    cities: ['Chersonissos', 'Heraklion', 'Psychro'],
    startDate: '2013-07-23',
    endDate: '2013-07-27',
  },
  {
    id: 'italy-2023',
    name: 'Italia 2023',
    country: 'Italy',
    cities: ['Florence', 'Pisa'],
    startDate: '2023-10-03',
    endDate: '2023-10-11',
  },
  {
    id: 'bosnia-2023',
    name: 'Bosnia 2023',
    country: 'Bosnia and Herzegovina',
    cities: ['Sarajevo', 'Jajce'],
    startDate: '2023-05-01',
    endDate: '2023-05-05',
  },
  {
    id: 'argentina-2025',
    name: 'Argentina 2025',
    country: 'Argentina',
    cities: ['Buenos Aires', 'Tigre', 'Rosario', 'Villa Traful', 'Bariloche', 'El Bolsón', 'Mendoza', 'Puente del Inca', 'Salta', 'Iguazú', 'Esteros del Iberá', 'Corrientes'],
    startDate: '2025-09-26',
    endDate: '2025-10-30',
  },
  {
    id: 'denmark-2024',
    name: 'Dinamarca 2024',
    country: 'Denmark',
    cities: ['Copenhagen', 'Hillerod'],
    startDate: '2024-09-15',
    endDate: '2024-09-20',
  },
];

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const OUTPUT_PATH = './resumen_fase1.json';
const MAPPING_PATH = './trip_mapping.json';

function findMatchingTrip(photoDate, photoCountry) {
  if (!photoDate || !photoCountry) return null;
  
  const dateStr = photoDate.split(' ')[0]; // Extract YYYY-MM-DD
  
  for (const trip of KNOWN_TRIPS) {
    // Check country match
    const tripCountries = trip.countries || [trip.country];
    if (!tripCountries.includes(photoCountry)) continue;
    
    // Check date range
    if (dateStr >= trip.startDate && dateStr <= trip.endDate) {
      return trip;
    }
  }
  
  return null;
}

function parseDate(dateStr) {
  if (!dateStr) return null;
  // Handle various formats
  const clean = dateStr.split(' ')[0]; // Remove time part
  if (/^\d{4}-\d{2}-\d{2}$/.test(clean)) return clean;
  return null;
}

async function main() {
  console.log('=== FASE 1: Asignación de Trips con KnownTrips.js ===');
  
  const db = new Database(DB_PATH);
  
  // 2. Get all photos with country and date
  const photos = db.prepare(`
    SELECT id, file_path, filename, date_taken, country, city, latitude, longitude
    FROM photos 
    WHERE country IS NOT NULL
  `).all();
  
  console.log(`📸 Fotos a procesar: ${photos.length}`);
  
  // 3. Assign trips
  const stats = {
    total: photos.length,
    assigned: 0,
    not_assigned: 0,
    by_trip: {},
    by_country: {},
    errors: [],
  };
  
  const tripMapping = {}; // photo_id -> trip_id
  
  for (const photo of photos) {
    try {
      const trip = findMatchingTrip(photo.date_taken, photo.country);
      
      if (trip) {
        tripMapping[photo.id] = trip.id;
        stats.assigned++;
        
        // Count by trip
        stats.by_trip[trip.id] = (stats.by_trip[trip.id] || 0) + 1;
      } else {
        stats.not_assigned++;
      }
      
      // Count by country
      stats.by_country[photo.country] = (stats.by_country[photo.country] || 0) + 1;
      
    } catch (e) {
      stats.errors.push({ id: photo.id, error: e.message });
    }
  }
  
  // Save mapping to file
  fs.writeFileSync(MAPPING_PATH, JSON.stringify(tripMapping, null, 2));
  console.log(`✅ Mapping guardado en: ${MAPPING_PATH}`);
  
  // 4. Get trip distribution from mapping
  const tripDist = {};
  for (const [photoId, tripId] of Object.entries(tripMapping)) {
    tripDist[tripId] = (tripDist[tripId] || 0) + 1;
  }
  
  stats.trip_distribution = Object.entries(tripDist)
    .map(([trip_id, cnt]) => ({ trip_id, cnt }))
    .sort((a, b) => b.cnt - a.cnt);
  
  // 5. Sample assigned photos
  const assignedIds = Object.keys(tripMapping).slice(0, 10);
  const samples = assignedIds.map(id => {
    const photo = photos.find(p => p.id === parseInt(id));
    return {
      id: photo.id,
      filename: photo.filename,
      date_taken: photo.date_taken,
      country: photo.country,
      trip_id: tripMapping[id]
    };
  });
  
  stats.samples = samples;
  
  // 6. Photos without trip (candidates for Phase 2-5)
  const noTripCounts = {};
  for (const photo of photos) {
    if (!tripMapping[photo.id]) {
      noTripCounts[photo.country] = (noTripCounts[photo.country] || 0) + 1;
    }
  }
  
  stats.no_trip_by_country = Object.entries(noTripCounts)
    .map(([country, cnt]) => ({ country, cnt }))
    .sort((a, b) => b.cnt - a.cnt);
  
  // 7. Write output
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(stats, null, 2));
  console.log(`\n✅ Resumen guardado en: ${OUTPUT_PATH}`);
  
  // 8. Print summary
  console.log('\n=== RESUMEN EJECUTIVO ===');
  console.log(`Total fotos: ${stats.total}`);
  console.log(`Asignadas a trip: ${stats.assigned} (${(stats.assigned/stats.total*100).toFixed(1)}%)`);
  console.log(`Sin trip: ${stats.not_assigned} (${(stats.not_assigned/stats.total*100).toFixed(1)}%)`);
  console.log('\nDistribución por viaje:');
  stats.trip_distribution.forEach(t => console.log(`  ${t.trip_id}: ${t.cnt}`));
  console.log('\nFotos sin trip por país:');
  stats.no_trip_by_country.forEach(c => console.log(`  ${c.country}: ${c.cnt}`));
  
  db.close();
}

main().catch(console.error);
