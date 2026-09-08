/**
 * H3Service - Servicio de indexación geoespacial con H3
 * Resolución 9: ~170m de lado por celda hexagonal
 */

import h3 from "h3-js";

const H3_RESOLUTION = 9;

export class H3Service {
  constructor(resolution = H3_RESOLUTION) {
    this.resolution = resolution;
  }

  /**
   * Convierte coordenadas (lat, lng) a índice H3
   * @param {number} lat - Latitud
   * @param {number} lng - Longitud
   * @returns {string} Índice H3
   */
  latLngToH3(lat, lng) {
    if (lat == null || lng == null) return null;
    try {
      return h3.latLngToCell(lat, lng, this.resolution);
    } catch (e) {
      return null;
    }
  }

  /**
   * Obtiene el centro de una celda H3
   * @param {string} h3Index - Índice H3
   * @returns {{lat: number, lng: number}}
   */
  h3ToLatLng(h3Index) {
    if (!h3Index) return null;
    try {
      const [lat, lng] = h3.cellToLatLng(h3Index);
      return { lat, lng };
    } catch (e) {
      return null;
    }
  }

  /**
   * Obtiene las celdas vecinas de un índice H3
   * @param {string} h3Index - Índice H3
   * @param {number} k - Número de anillos de vecinos
   * @returns {string[]} Array de índices H3 vecinos
   */
  getNeighbors(h3Index, k = 1) {
    if (!h3Index) return [];
    try {
      return h3.gridDisk(h3Index, k);
    } catch (e) {
      return [];
    }
  }

  /**
   * Calcula la distancia entre dos celdas H3 en número de pasos
   * @param {string} h3_1 - Primer índice H3
   * @param {string} h3_2 - Segundo índice H3
   * @returns {number} Distancia en pasos (0 = misma celda)
   */
  h3Distance(h3_1, h3_2) {
    if (!h3_1 || !h3_2) return Infinity;
    try {
      return h3.gridDistance(h3_1, h3_2);
    } catch (e) {
      return Infinity;
    }
  }

  /**
   * Verifica si dos celdas H3 son adyacentes o están dentro de un umbral
   * @param {string} h3_1 - Primer índice H3
   * @param {string} h3_2 - Segundo índice H3
   * @param {number} maxDistance - Distancia máxima en pasos H3
   * @returns {boolean}
   */
  areNearby(h3_1, h3_2, maxDistance = 2) {
    if (h3_1 === h3_2) return true;
    const distance = this.h3Distance(h3_1, h3_2);
    return distance <= maxDistance;
  }

  /**
   * Obtiene el índice H3 de una resolución inferior (área más grande)
   * @param {string} h3Index - Índice H3
   * @param {number} resolution - Resolución objetivo
   * @returns {string}
   */
  h3ToParent(h3Index, resolution) {
    if (!h3Index) return null;
    try {
      return h3.cellToParent(h3Index, resolution);
    } catch (e) {
      return null;
    }
  }

  getResolution() {
    return this.resolution;
  }
}

export default new H3Service();