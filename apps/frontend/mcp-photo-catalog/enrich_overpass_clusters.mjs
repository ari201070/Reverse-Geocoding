/**
 * enrich_overpass_clusters.mjs
 * 
 * Script de Enriquecimiento Geográfico Masivo con Overpass API + Photon Backup (OpenStreetMap)
 * Siguiendo las directivas del Arquitecto.
 */

import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const RESUMEN_PATH = path.join(__dirname, 'resumen_proceso.json');

// Overpass API Endpoints (priorizando el endpoint probado más rápido)
const OVERPASS_ENDPOINTS = [
  'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
  'https://overpass-api.de/api/interpreter',
  'https://lz4.overpass-api.de/api/interpreter'
];

const DELAY_BETWEEN_REQUESTS_MS = 1100; // 1.1s para margen de seguridad
const BATCH_SIZE = 50;
const MAX_RETRIES = 3;
const USER_AGENT = 'TravelBookingDocumentHub/1.0 (contact@example.com)';

const delay = (ms) => new Promise((res) => setTimeout(res, ms));

/**
 * Inicializa la tabla de control de progreso en la base de datos
 */
function initProgressTable(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS overpass_clusters_progress (
      cluster_id TEXT PRIMARY KEY,
      lat_cluster REAL NOT NULL,
      lon_cluster REAL NOT NULL,
      centroid_lat REAL NOT NULL,
      centroid_lon REAL NOT NULL,
      photo_count INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'PENDING',
      location_name_found TEXT,
      last_attempt_timestamp TEXT,
      retry_count INTEGER DEFAULT 0
    )
  `);
}

/**
 * Sincroniza la cola de clusters sin hardcodear (dinámico desde DB)
 */
function syncClusterQueue(db) {
  initProgressTable(db);

  const clusters = db.prepare(`
    SELECT 
      ROUND(latitude, 3) as lat_cluster, 
      ROUND(longitude, 3) as lon_cluster,
      AVG(latitude) as centroid_lat,
      AVG(longitude) as centroid_lon,
      COUNT(*) as photo_count
    FROM photos 
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude != 0 AND longitude != 0
      AND (location_name IS NULL OR location_name = '')
    GROUP BY lat_cluster, lon_cluster
    ORDER BY photo_count DESC
  `).all();

  const insertStmt = db.prepare(`
    INSERT OR IGNORE INTO overpass_clusters_progress 
    (cluster_id, lat_cluster, lon_cluster, centroid_lat, centroid_lon, photo_count, status)
    VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
  `);

  let newClusters = 0;
  const insertMany = db.transaction((rows) => {
    for (const row of rows) {
      const clusterId = `${row.lat_cluster}_${row.lon_cluster}`;
      const res = insertStmt.run(clusterId, row.lat_cluster, row.lon_cluster, row.centroid_lat, row.centroid_lon, row.photo_count);
      if (res.changes > 0) newClusters++;
    }
  });

  insertMany(clusters);
  return clusters.length;
}

/**
 * Construye la query Overpass QL
 */
function buildOverpassQuery(lat, lon) {
  return `[out:json][timeout:15];
(
  node(around:250, ${lat}, ${lon})[name][~"^(tourism|natural|peak|route|historic|amenity|attraction|information)$"~".*"];
  way(around:250, ${lat}, ${lon})[name][~"^(tourism|natural|peak|route|historic|amenity|attraction|information)$"~".*"];
  relation(around:250, ${lat}, ${lon})[name][~"^(tourism|natural|peak|route|historic|amenity|attraction|information)$"~".*"];
);
out center 10;`;
}

/**
 * Consulta Overpass API con failover
 */
async function queryOverpass(lat, lon) {
  const query = buildOverpassQuery(lat, lon);

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const endpoint = OVERPASS_ENDPOINTS[attempt % OVERPASS_ENDPOINTS.length];
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/x-www-form-urlencoded',
          'User-Agent': USER_AGENT
        },
        body: `data=${encodeURIComponent(query)}`,
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        const name = parseOverpassPOIName(data);
        if (name) return name;
      }
    } catch (err) {
      // Continuar al siguiente intento/proveedor
    }
    
    await delay(500);
  }

  // Fallback a Photon API (OpenStreetMap Komoot)
  return await queryPhotonFallback(lat, lon);
}

/**
 * Fallback a Photon API
 */
async function queryPhotonFallback(lat, lon) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const url = `https://photon.komoot.io/reverse?lat=${lat}&lon=${lon}&lang=en`;
    const response = await fetch(url, {
      headers: { 'User-Agent': USER_AGENT },
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      const props = data.features?.[0]?.properties;
      if (props) {
        return props.name || props.street || props.city || props.district || null;
      }
    }
  } catch (e) {
    // Ignorar fallback error
  }
  return null;
}

/**
 * Extrae el mejor nombre de POI de Overpass
 */
function parseOverpassPOIName(data) {
  if (!data?.elements || data.elements.length === 0) return null;

  const namedElements = data.elements.filter(e => e.tags && e.tags.name);
  if (namedElements.length === 0) return null;

  const priorityTypes = ['tourism', 'historic', 'attraction', 'natural', 'peak', 'route', 'amenity', 'information'];
  
  namedElements.sort((a, b) => {
    const aType = Object.keys(a.tags).find(k => priorityTypes.includes(k));
    const bType = Object.keys(b.tags).find(k => priorityTypes.includes(k));
    
    const aWeight = aType ? priorityTypes.indexOf(aType) : 99;
    const bWeight = bType ? priorityTypes.indexOf(bType) : 99;
    
    return aWeight - bWeight;
  });

  return namedElements[0].tags.name;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  AGENTE DE INGENIERÍA DE DATOS: ENRIQUECIMIENTO OVERPASS API');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const db = new Database(DB_PATH);

  // 1. Estadísticas dinámicas del catálogo
  const totalPhotosInDb = db.prepare('SELECT COUNT(*) as c FROM photos').get().c;
  const gpsPhotosInDb = db.prepare('SELECT COUNT(*) as c FROM photos WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude != 0 AND longitude != 0').get().c;
  const unmappedPhotosInDb = db.prepare('SELECT COUNT(*) as c FROM photos WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude != 0 AND longitude != 0 AND (location_name IS NULL OR location_name = \'\')').get().c;

  console.log(`📊 ESTADÍSTICAS DINÁMICAS DEL CATÁLOGO:`);
  console.log(`   - Total de fotos en DB:                 ${totalPhotosInDb.toLocaleString()}`);
  console.log(`   - Fotos con GPS válido:                 ${gpsPhotosInDb.toLocaleString()}`);
  console.log(`   - Fotos pendientes de location_name:   ${unmappedPhotosInDb.toLocaleString()}\n`);

  if (unmappedPhotosInDb === 0) {
    console.log('🎉 ¡Todas las fotos geolocalizadas ya tienen un location_name asignado!');
    db.close();
    return;
  }

  // 2. Sincronizar cola de clusters en DB
  const totalClusters = syncClusterQueue(db);
  console.log(`🗺️  Cola de clusters espaciales (~100m) sincronizada: ${totalClusters} clusters únicos.\n`);

  // 3. Obtener clusters pendientes
  const pendingClusters = db.prepare(`
    SELECT * FROM overpass_clusters_progress 
    WHERE status IN ('PENDING', 'FAILED')
    ORDER BY photo_count DESC
  `).all();

  const totalToProcess = pendingClusters.length;
  const completedSoFar = db.prepare(`SELECT COUNT(*) as c FROM overpass_clusters_progress WHERE status IN ('COMPLETED', 'NO_POI')`).get().c;

  console.log(`🚀 Clusters pendientes por procesar: ${totalToProcess} (Completados previamente: ${completedSoFar})\n`);

  if (totalToProcess === 0) {
    console.log('✅ Todos los clusters ya han sido procesados previamente.');
    db.close();
    return;
  }

  // Sentencias preparadas
  const updateProgressStmt = db.prepare(`
    UPDATE overpass_clusters_progress 
    SET status = ?, location_name_found = ?, last_attempt_timestamp = datetime('now'), retry_count = retry_count + 1
    WHERE cluster_id = ?
  `);

  const bulkUpdatePhotosStmt = db.prepare(`
    UPDATE photos 
    SET location_name = ?
    WHERE ROUND(latitude, 3) = ? AND ROUND(longitude, 3) = ?
      AND (location_name IS NULL OR location_name = '')
  `);

  let totalPhotosUpdated = 0;
  let poisFoundCount = 0;
  let noPoiCount = 0;

  // 4. Procesar en batches de 50
  for (let i = 0; i < pendingClusters.length; i += BATCH_SIZE) {
    const batch = pendingClusters.slice(i, i + BATCH_SIZE);
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(pendingClusters.length / BATCH_SIZE);

    console.log(`\n📦 --- PROCESANDO BATCH ${batchNum} DE ${totalBatches} (${batch.length} clusters) ---`);

    for (let j = 0; j < batch.length; j++) {
      const cluster = batch[j];
      const globalIndex = completedSoFar + i + j + 1;

      // Marcar PROCESSING
      db.prepare(`UPDATE overpass_clusters_progress SET status = 'PROCESSING' WHERE cluster_id = ?`).run(cluster.cluster_id);

      // Delay obligatorio de 1.1s entre llamadas
      await delay(DELAY_BETWEEN_REQUESTS_MS);

      const poiName = await queryOverpass(cluster.centroid_lat, cluster.centroid_lon);

      if (poiName) {
        updateProgressStmt.run('COMPLETED', poiName, cluster.cluster_id);
        const updateRes = bulkUpdatePhotosStmt.run(poiName, cluster.lat_cluster, cluster.lon_cluster);
        totalPhotosUpdated += updateRes.changes;
        poisFoundCount++;

        console.log(`  [PROGRESO] Cluster ${globalIndex} de ${totalClusters} (${cluster.photo_count} fotos) → 📍 POI: "${poiName}" (Saturación: ${updateRes.changes} fotos actualizadas)`);
      } else {
        updateProgressStmt.run('NO_POI', null, cluster.cluster_id);
        noPoiCount++;

        console.log(`  [PROGRESO] Cluster ${globalIndex} de ${totalClusters} (${cluster.photo_count} fotos) → ⚠️ Sin POI destacado en 250m`);
      }
    }

    console.log(`\n✅ Batch ${batchNum} completado. Total fotos actualizadas acumuladas: ${totalPhotosUpdated}`);
  }

  // 5. Resumen final
  const finalUnmapped = db.prepare('SELECT COUNT(*) as c FROM photos WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude != 0 AND longitude != 0 AND (location_name IS NULL OR location_name = \'\')').get().c;

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  🎉 RESUMEN FINAL DE ENRIQUECIMIENTO CON OVERPASS API');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`  📸 Fotos actualizadas con location_name: ${totalPhotosUpdated.toLocaleString()}`);
  console.log(`  📍 Clusters con POI encontrado:            ${poisFoundCount}`);
  console.log(`  ⚠️ Clusters sin POI en 250m:                ${noPoiCount}`);
  console.log(`  ❓ Fotos con GPS aún sin location_name:   ${finalUnmapped.toLocaleString()}`);
  console.log('═══════════════════════════════════════════════════════════════\n');

  // 6. Guardar resumen en JSON
  const resumen = {
    fecha_ejecucion: new Date().toISOString(),
    estadisticas: {
      total_fotos_db: totalPhotosInDb,
      fotos_con_gps: gpsPhotosInDb,
      fotos_pendientes_location: unmappedPhotosInDb,
    },
    resultados_enriquecimiento: {
      clusters_procesados: totalClusters,
      clusters_con_poi: poisFoundCount,
      clusters_sin_poi: noPoiCount,
      fotos_actualizadas: totalPhotosUpdated,
    },
    estado_final: {
      fotos_con_location_name: totalPhotosInDb - finalUnmapped,
      fotos_sin_location_name: finalUnmapped,
    }
  };

  fs.writeFileSync(RESUMEN_PATH, JSON.stringify(resumen, null, 2));
  console.log(`📄 Resumen guardado en: ${RESUMEN_PATH}`);

  db.close();
}

main().catch(err => {
  console.error('❌ Error fatal en enrich_overpass_clusters:', err);
  process.exit(1);
});
