/**
 * SpatialCacheClient - Caché espacial local para consultas geoespacial
 * Almacena resultados de H3 y geocodificación para evitar llamadas repetidas
 */

import h3Service from "./H3Service.js";

export class SpatialCacheClient {
  constructor() {
    // Caché en memoria: h3Index → { country, city, locationName, confidence }
    this.cache = new Map();
    
    // Estadísticas
    this.stats = {
      hits: 0,
      misses: 0,
      entries: 0,
    };
  }

  /**
   * Obtiene datos de caché para una coordenada
   * @param {number} lat - Latitud
   * @param {number} lng - Longitud
   * @returns {Object|null} Datos en caché o null
   */
  get(lat, lng) {
    const h3Index = h3Service.latLngToH3(lat, lng);
    if (!h3Index) return null;
    
    const cached = this.cache.get(h3Index);
    if (cached) {
      this.stats.hits++;
      return { ...cached, h3Index, fromCache: true };
    }
    
    this.stats.misses++;
    return null;
  }

  /**
   * Almacena datos en la caché espacial
   * @param {number} lat - Latitud
   * @param {number} lng - Longitud
   * @param {Object} data - Datos a almacenar
   */
  set(lat, lng, data) {
    const h3Index = h3Service.latLngToH3(lat, lng);
    if (!h3Index) return;
    
    this.cache.set(h3Index, {
      ...data,
      h3Index,
      timestamp: Date.now(),
    });
    this.stats.entries = this.cache.size;
  }

  /**
   * Obtiene o calcula datos para una coordenada
   * @param {number} lat - Latitud
   * @param {number} lng - Longitud
   * @param {Function} computeFn - Función para calcular si no está en caché
   * @returns {Object} Datos de la coordenada
   */
  async getOrCompute(lat, lng, computeFn) {
    const cached = this.get(lat, lng);
    if (cached) return cached;
    
    const h3Index = h3Service.latLngToH3(lat, lng);
    const computed = await computeFn(lat, lng, h3Index);
    
    this.set(lat, lng, computed);
    return { ...computed, h3Index, fromCache: false };
  }

  /**
   * Verifica si dos coordenadas están en la misma celda H3 o vecinas
   * @param {number} lat1 - Latitud punto 1
   * @param {number} lng1 - Longitud punto 1
   * @param {number} lat2 - Latitud punto 2
   * @param {number} lng2 - Longitud punto 2
   * @param {number} maxDistance - Distancia máxima en pasos H3
   * @returns {boolean}
   */
  areNearby(lat1, lng1, lat2, lng2, maxDistance = 2) {
    const h3_1 = h3Service.latLngToH3(lat1, lng1);
    const h3_2 = h3Service.latLngToH3(lat2, lng2);
    return h3Service.areNearby(h3_1, h3_2, maxDistance);
  }

  /**
   * Obtiene todas las entradas de la caché para un área
   * @param {number} lat - Latitud centro
   * @param {number} lng - Longitud centro
   * @param {number} radius - Radio en pasos H3
   * @returns {Array} Entradas de caché en el área
   */
  getInArea(lat, lng, radius = 2) {
    const centerH3 = h3Service.latLngToH3(lat, lng);
    if (!centerH3) return [];
    
    const neighbors = h3Service.getNeighbors(centerH3, radius);
    return neighbors
      .map(h3 => this.cache.get(h3))
      .filter(entry => entry != null);
  }

  /**
   * Limpia la caché
   */
  clear() {
    this.cache.clear();
    this.stats = { hits: 0, misses: 0, entries: 0 };
  }

  /**
   * Obtiene estadísticas de la caché
   */
  getStats() {
    return {
      ...this.stats,
      hitRate: this.stats.hits + this.stats.misses > 0
        ? (this.stats.hits / (this.stats.hits + this.stats.misses) * 100).toFixed(1) + '%'
        : '0%',
    };
  }
}

export default new SpatialCacheClient();