import { latLngToCell } from 'h3-js';

const TIME_WINDOW_S = 3600;      // 60 minutos: ventana de agrupamiento (Stress Test Rule)
const INHERIT_WINDOW_S = 900;    // 15 minutos: herencia de ubicación para fotos sin GPS (Stress Test Rule)
const H3_RESOLUTION = 9;         // ~170m hexágonos

/**
 * Redondea coordenadas a 4 decimales (~11m) para privacidad y cache hits (Stress Test Rule).
 */
function roundCoord(val) {
  return Math.round(val * 10000) / 10000;
}

/**
 * Selecciona la mejor foto ancla del grupo:
 * - Prioriza Landmarks > OCR > Labels
 */
function pickAnchor(photos) {
  const withGps = photos.filter(p => p.lat != null && p.lng != null);
  
  // Si no hay GPS, buscamos la mejor señal visual en el lote
  const candidates = photos.filter(p => p.visionLandmarks?.length > 0 || p.visionTexts?.length > 0 || p.visionLabels?.length > 0);
  
  if (!candidates.length && !withGps.length) return null;

  // Sistema de puntuación (v3.2)
  const scored = (candidates.length ? candidates : withGps).map(p => {
    let score = 0;
    if (p.visionLandmarks?.length > 0) score = 100;
    else if (p.visionTexts?.length > 0 && p.visionTexts[0].length < 60) score = 80;
    else if (p.lat != null) score = 50;
    else if (p.visionLabels?.length > 0) score = 10;
    
    return { ...p, internalScore: score };
  });

  return scored.sort((a, b) => b.internalScore - a.internalScore || (a.timestamp - b.timestamp))[0];
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

    // Ruptura temporal (60 min)
    if (timeDiff > TIME_WINDOW_S) {
      clusters.push(finalizeCluster(current));
      current = [photo];
      anchorH3 = photo.lat != null
        ? latLngToCell(roundCoord(photo.lat), roundCoord(photo.lng), H3_RESOLUTION)
        : null;
      continue;
    }

    // Ruptura espacial (H3 Res 9)
    if (photo.lat != null && anchorH3) {
      const photoH3 = latLngToCell(roundCoord(photo.lat), roundCoord(photo.lng), H3_RESOLUTION);
      if (photoH3 !== anchorH3) {
        clusters.push(finalizeCluster(current));
        current = [photo];
        anchorH3 = photoH3;
        continue;
      }
    }

    if (photo.lat != null && !anchorH3) {
      anchorH3 = latLngToCell(roundCoord(photo.lat), roundCoord(photo.lng), H3_RESOLUTION);
    }

    current.push(photo);
  }

  if (current.length) clusters.push(finalizeCluster(current));
  return clusters;
}

function finalizeCluster(photos) {
  const anchor = pickAnchor(photos);

  if (anchor && anchor.lat != null) {
    for (const p of photos) {
      if (p.lat == null && p.lng == null) {
        const diff = Math.abs(p.timestamp - anchor.timestamp) / 1000;
        if (diff <= INHERIT_WINDOW_S) {
          p.lat = anchor.lat;
          p.lng = anchor.lng;
          p.inherited = true;
          p.inheritanceSource = anchor.id;
        }
      }
    }
  }

  return {
    anchor,
    h3Index: anchor && anchor.lat != null ? latLngToCell(roundCoord(anchor.lat), roundCoord(anchor.lng), H3_RESOLUTION) : null,
    photos,
    count: photos.length,
  };
}
