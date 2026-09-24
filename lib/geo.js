/**
 * Parsea un string de fecha EXIF estándar (YYYY:MM:DD HH:MM:SS) de forma segura.
 */
export function parseExif(s) {
  if (!s) return null;
  const m = s.match(/(\d{4}):(\d{2}):(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);
  return m 
    ? new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]) 
    : new Date(s.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3'));
}

/**
 * Calcula la distancia Haversine (ortodrómica) entre dos puntos geográficos en KM.
 */
export function calculateHaversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radio de la Tierra en KM
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Calcula la similitud coseno entre dos vectores numéricos (DINOv2 / CLIP).
 */
export function calculateCosineSimilarity(vecA, vecB) {
  if (!vecA || !vecB || vecA.length !== vecB.length) return 0;
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  return normA === 0 || normB === 0 ? 0 : dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}
