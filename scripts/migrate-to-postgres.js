import Database from 'better-sqlite3';
import { query } from '../lib/pg_db.js';
import { parseExif, calculateHaversineDistance } from '../lib/geo.js';
import { latLngToCell } from 'h3-js';
import path from 'path';

const legacyDbPath = path.resolve(process.cwd(), 'data/photo_catalog.db');
const db = new Database(legacyDbPath, { fileMustExist: true });

// 1. LA TABLA DE VERDAD DEL VIAJE (Basada estrictamente en tus Vouchers y Agenda)
const ITINERARY_VOUCHERS = {
  "2023-04-18": {
    region: "Sarajevo (Tunnel of Hope)",
    center_lat: 43.8242,
    center_lng: 18.3831,
    allowed_radius_km: 15.0
  },
  "2023-04-19": {
    region: "Konjic (Bunker de Tito ARK D-0)",
    center_lat: 43.6514,
    center_lng: 17.9625,
    allowed_radius_km: 10.0
  }
};

async function executeSpatialMigration() {
  console.log("🚀 [MIGRACIÓN + CALENDARIO] Iniciando volcado con Auto-Corrección por Vouchers...");
  
  try {
    const photos = db.prepare(`
      SELECT photo_name, date_taken, latitude, longitude, camera_heading 
      FROM photos 
      WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL 
        AND (place_name IS NULL OR place_name != 'pending_osint')
    `).all();

    console.log(`📦 Lote físico a procesar: ${photos.length} registros.`);
    let insertedCount = 0;
    let autoCorrectedCount = 0;

    for (const photo of photos) {
      let finalLat = photo.latitude;
      let finalLng = photo.longitude;
      let isCorrected = false;

      if (photo.date_taken) {
        const dateKey = photo.date_taken.split(' ')[0].replace(/:/g, '-');
        const voucher = ITINERARY_VOUCHERS[dateKey];
        if (voucher) {
          const deviationKm = calculateHaversineDistance(finalLat, finalLng, voucher.center_lat, voucher.center_lng);
          if (deviationKm > voucher.allowed_radius_km) {
            finalLat = voucher.center_lat;
            finalLng = voucher.center_lng;
            isCorrected = true;
            autoCorrectedCount++;
            console.log(`⚠️ [AUTO-CORRECCIÓN] \`${path.basename(photo.photo_name)}\` desviada por ${deviationKm.toFixed(1)}km del voucher. Re-ubicada en: ${voucher.region}`);
          }
        }
      }

      const realH3Index = latLngToCell(finalLat, finalLng, 9);

      const sql = `
        INSERT INTO spatial_cache (
          photo_name, 
          date_taken, 
          camera_heading, 
          h3_index, 
          geom
        ) VALUES ($1, $2, $3, $4, ST_SetSRID(ST_MakePoint($5, $6), 4326))
        ON CONFLICT (photo_name) DO UPDATE SET
          date_taken = EXCLUDED.date_taken,
          camera_heading = EXCLUDED.camera_heading,
          h3_index = EXCLUDED.h3_index,
          geom = EXCLUDED.geom,
          indexed_at = CURRENT_TIMESTAMP;
      `;

      const params = [
        photo.photo_name,
        photo.date_taken,
        photo.camera_heading || null,
        realH3Index,
        finalLng,
        finalLat
      ];

      await query(sql, params);
      insertedCount++;
    }

    console.log(`\n✨ [MIGRACIÓN CON CALENDARIO EXITOSA]`);
    console.log(`- Total procesado en PostGIS: ${insertedCount}/${photos.length}`);
    console.log(`- Fotos auto-corregidas por desvío de Voucher: ${autoCorrectedCount}`);
    
    db.close();

  } catch (error) {
    console.error("🚨 [ERROR CRÍTICO] La migración con calendario falló:", error.message);
    process.exit(1);
  }
}

executeSpatialMigration();
