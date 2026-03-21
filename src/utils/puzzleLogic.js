import { latLngToCell } from 'h3-js';

const TIME_WINDOW_S = 3600;      // 60 minutos: ventana de agrupamiento
const INHERIT_WINDOW_S = 900;    // 15 minutos: herencia de ubicación para fotos sin GPS
const H3_RESOLUTION = 9;         // ~170m hexágonos

/**
 * Redondea coordenadas a 4 decimales (~11m) para privacidad y cache hits.
 */
function roundCoord(val) {
  return Math.round(val * 10000) / 10000;
}

/**
 * Selecciona la mejor foto ancla del grupo:
 * - Prioriza confianza OCR/Hitos > 90%
 * - Luego menor radio de precisión EXIF (GPSHPositioningError)
 */
function pickAnchor(photos) {
  const withGps = photos.filter(p => p.lat != null && p.lng != null);
  if (!withGps.length) return null;

  // Prioridad 1: OCR/Hitos con confianza > 90%
  const highConf = withGps.filter(p => (p.ocrConfidence || 0) > 0.9 || (p.landmarkConfidence || 0) > 0.9);
  if (highConf.length) {
    return highConf.reduce((best, p) => ((p.gpsAccuracy || Infinity) < (best.gpsAccuracy || Infinity) ? p : best));
  }

  // Prioridad 2: Mejor precisión EXIF
  return withGps.reduce((best, p) => ((p.gpsAccuracy || Infinity) < (best.gpsAccuracy || Infinity) ? p : best));
}

/**
 * Clustering espacial y temporal de fotos antes de subida.
 * Reglas:
 *  - Ventana temporal: 60 min entre fotos consecutivas
 *  - Ruptura espacial: cambio de celda H3 res9 (~170m)
 *  - Herencia: fotos sin GPS heredan ubicación del ancla si están a <15 min
 */
export function clusterPhotos(photos) {
  if (!photos.length) return [];

  // Ordenar por timestamp
  const sorted = [...photos].sort((a, b) => a.timestamp - b.timestamp);
  const clusters = [];
  let current = [sorted[0]];
  let anchorH3 = null;

  if (sorted[0].lat != null) {
    anchorH3 = latLngToCell(roundCoord(sorted[0].lat), roundCoord(sorted[0].lng), H3_RESOLUTION);
  }

  for (let i = 1; i < sorted.length; i++) {
    const photo = sorted[i];
    const prev = sorted[i - 1];
    const timeDiff = Math.abs(photo.timestamp - prev.timestamp) / 1000;

    // Ruptura temporal
    if (timeDiff > TIME_WINDOW_S) {
      clusters.push(finalizeCluster(current));
      current = [photo];
      anchorH3 = photo.lat != null
        ? latLngToCell(roundCoord(photo.lat), roundCoord(photo.lng), H3_RESOLUTION)
        : null;
      continue;
    }

    // Ruptura espacial: si la foto tiene GPS y su H3 difiere del ancla
    if (photo.lat != null && anchorH3) {
      const photoH3 = latLngToCell(roundCoord(photo.lat), roundCoord(photo.lng), H3_RESOLUTION);
      if (photoH3 !== anchorH3) {
        clusters.push(finalizeCluster(current));
        current = [photo];
        anchorH3 = photoH3;
        continue;
      }
    }

    // Actualizar ancla H3 si la foto actual tiene GPS y no había ancla
    if (photo.lat != null && !anchorH3) {
      anchorH3 = latLngToCell(roundCoord(photo.lat), roundCoord(photo.lng), H3_RESOLUTION);
    }

    current.push(photo);
  }

  if (current.length) clusters.push(finalizeCluster(current));
  return clusters;
}

/**
 * Finaliza un clúster: elige ancla, hereda ubicación a fotos sin GPS.
 */
function finalizeCluster(photos) {
  const anchor = pickAnchor(photos);

  // Herencia: fotos sin GPS heredan del ancla si están a <15 min
  if (anchor) {
    for (const p of photos) {
      if (p.lat == null && p.lng == null) {
        const diff = Math.abs(p.timestamp - anchor.timestamp) / 1000;
        if (diff <= INHERIT_WINDOW_S) {
          p.lat = anchor.lat;
          p.lng = anchor.lng;
          p.inherited = true;
        }
      }
    }
  }

  return {
    anchor,
    h3Index: anchor ? latLngToCell(roundCoord(anchor.lat), roundCoord(anchor.lng), H3_RESOLUTION) : null,
    photos,
    count: photos.length,
  };
}
