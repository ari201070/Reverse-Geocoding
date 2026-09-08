/**
 * ConsensusEngine - Motor de Consenso y Prudencia Agéntica (Antigravity 2.0)
 * 
 * Sistema de scoring ponderado que determina si una foto pertenece a un viaje específico.
 * 
 * Fuentes de evidencia:
 * - Evidencia Fuerte: Reservas de vuelos/hoteles (H3 + fecha)
 * - Evidencia Espacial: Proximidad H3 entre fotos
 * - Evidencia Temporal: Ventana de fechas del viaje
 * - Evidencia Nominal: Coincidencia de país
 * - Confianza de Geolocalización: Calidad del GPS y reverse geocoding
 * 
 * Thresholds:
 * - >= 75%: Asignación automática
 * - 50-74%: Verificación requerida (HITL)
 * - < 50%: Revisión humana
 */

import h3Service from "./H3Service.js";

// Pesos para el cálculo de confianza
const WEIGHTS = {
  BOOKING_MATCH: 0.40,      // Coincidencia con reservas
  SPATIAL_PROXIMITY: 0.25,  // Proximidad H3
  TEMPORAL_PROXIMITY: 0.20, // Proximidad temporal
  COUNTRY_MATCH: 0.10,      // Coincidencia de país
  GPS_QUALITY: 0.05,        // Calidad del GPS
};

// Thresholds de confianza
const THRESHOLDS = {
  AUTO_ASSIGN: 0.75,    // Asignación automática
  HITL_VERIFY: 0.50,    // Requiere verificación humana
  // < 0.50: Revisión humana completa
};

// Tiempo máximo entre fotos para considerarlas del mismo "cluster" (en milisegundos)
const CLUSTER_TIME_WINDOW = 5 * 60 * 1000; // 5 minutos

// Distancia máxima H3 para considerar fotos cercanas
const MAX_H3_DISTANCE = 2;

export class ConsensusEngine {
  constructor() {
    this.weights = WEIGHTS;
    this.thresholds = THRESHOLDS;
  }

  /**
   * Evalúa si una foto pertenece a un viaje candidato
   * @param {Object} photo - Foto a evaluar
   * @param {Object} trip - Viaje candidato
   * @param {Array} tripPhotos - Fotos ya asignadas al viaje
   * @param {Object} bookingData - Datos de reservas (opcional)
   * @returns {Object} { confidence, assignment, reason }
   */
  evaluatePhoto(photo, trip, tripPhotos = [], bookingData = null) {
    const scores = {
      bookingMatch: this._scoreBookingMatch(photo, trip, bookingData),
      spatialProximity: this._scoreSpatialProximity(photo, tripPhotos),
      temporalProximity: this._scoreTemporalProximity(photo, trip),
      countryMatch: this._scoreCountryMatch(photo, trip),
      gpsQuality: this._scoreGpsQuality(photo),
    };

    // Calcular confianza total ponderada
    const confidence = 
      scores.bookingMatch * this.weights.BOOKING_MATCH +
      scores.spatialProximity * this.weights.SPATIAL_PROXIMITY +
      scores.temporalProximity * this.weights.TEMPORAL_PROXIMITY +
      scores.countryMatch * this.weights.COUNTRY_MATCH +
      scores.gpsQuality * this.weights.GPS_QUALITY;

    // Determinar asignación según threshold
    let assignment;
    let reason;
    
    if (confidence >= this.thresholds.AUTO_ASSIGN) {
      assignment = 'AUTO';
      reason = 'Alta confianza: asignación automática';
    } else if (confidence >= this.thresholds.HITL_VERIFY) {
      assignment = 'VERIFY';
      reason = 'Confianza media: requiere verificación';
    } else {
      assignment = 'AMBIGUOUS';
      reason = 'Baja confianza: revisión humana requerida';
    }

    return {
      confidence: Math.round(confidence * 100) / 100,
      assignment,
      reason,
      scores,
    };
  }

  /**
   * Score de coincidencia con reservas (evidencia fuerte)
   */
  _scoreBookingMatch(photo, trip, bookingData) {
    if (!bookingData || !photo.h3Index) return 0;
    
    // Verificar si hay reservas que coincidan con el H3 y fecha de la foto
    const photoDate = photo.bestDate;
    if (!photoDate) return 0;
    
    let maxScore = 0;
    
    for (const booking of bookingData) {
      // Verificar coincidencia temporal
      if (booking.startDate && booking.endDate) {
        const bookingStart = new Date(booking.startDate);
        const bookingEnd = new Date(booking.endDate);
        
        if (photoDate >= bookingStart && photoDate <= bookingEnd) {
          // Verificar coincidencia espacial si la reserva tiene coordenadas
          if (booking.latitude && booking.longitude) {
            const bookingH3 = h3Service.latLngToH3(booking.latitude, booking.longitude);
            if (h3Service.areNearby(photo.h3Index, bookingH3, MAX_H3_DISTANCE)) {
              maxScore = Math.max(maxScore, 1.0);
            }
          } else {
            // Solo coincidencia temporal
            maxScore = Math.max(maxScore, 0.6);
          }
        }
      }
    }
    
    return maxScore;
  }

  /**
   * Score de proximidad espacial (H3)
   */
  _scoreSpatialProximity(photo, tripPhotos) {
    if (!photo.h3Index || tripPhotos.length === 0) return 0;
    
    let nearbyCount = 0;
    let totalDistance = 0;
    
    for (const otherPhoto of tripPhotos) {
      if (!otherPhoto.h3Index) continue;
      
      const distance = h3Service.h3Distance(photo.h3Index, otherPhoto.h3Index);
      if (distance <= MAX_H3_DISTANCE) {
        nearbyCount++;
        totalDistance += distance;
      }
    }
    
    if (nearbyCount === 0) return 0;
    
    // Normalizar: más fotos cercanas = mayor score
    const proximityRatio = nearbyCount / tripPhotos.length;
    const avgDistance = totalDistance / nearbyCount;
    
    // Score basado en proporción de fotos cercanas y distancia promedio
    return Math.min(1.0, proximityRatio * (1 - avgDistance / (MAX_H3_DISTANCE + 1)));
  }

  /**
   * Score de proximidad temporal
   */
  _scoreTemporalProximity(photo, trip) {
    if (!photo.bestDate || !trip.startDate || !trip.endDate) return 0;
    
    const photoTime = photo.bestDate.getTime();
    const tripStart = new Date(trip.startDate).getTime();
    const tripEnd = new Date(trip.endDate).getTime();
    
    // Verificar si la foto está dentro del rango del viaje
    if (photoTime >= tripStart && photoTime <= tripEnd) {
      return 1.0;
    }
    
    // Calcular distancia al rango más cercano
    const distToStart = Math.abs(photoTime - tripStart);
    const distToEnd = Math.abs(photoTime - tripEnd);
    const minDist = Math.min(distToStart, distToEnd);
    
    // Penalizar por cada día de diferencia
    const daysDiff = minDist / (24 * 60 * 60 * 1000);
    
    if (daysDiff <= 1) return 0.8;
    if (daysDiff <= 3) return 0.6;
    if (daysDiff <= 7) return 0.4;
    if (daysDiff <= 14) return 0.2;
    return 0;
  }

  /**
   * Score de coincidencia de país
   */
  _scoreCountryMatch(photo, trip) {
    if (!photo.country || !trip.countries) return 0;
    
    const photoCountry = photo.country.trim().toLowerCase();
    const tripCountries = trip.countries.map(c => c.trim().toLowerCase());
    
    if (tripCountries.includes(photoCountry)) {
      return 1.0;
    }
    
    return 0;
  }

  /**
   * Score de calidad del GPS
   */
  _scoreGpsQuality(photo) {
    if (!photo.latitude || !photo.longitude) return 0;
    
    // Score base por tener coordenadas
    let score = 0.5;
    
    // Bonus si tiene precisión GPS
    if (photo.gpsAccuracy) {
      const accuracy = parseFloat(photo.gpsAccuracy);
      if (accuracy <= 10) score = 1.0;      // Muy precisa
      else if (accuracy <= 30) score = 0.8;  // Buena
      else if (accuracy <= 100) score = 0.6; // Aceptable
      else score = 0.4;                      // Baja
    }
    
    return score;
  }

  /**
   * Determina si una foto debe ser marcada como "no asignada"
   * @param {Object} photo - Foto a evaluar
   * @param {Array} allTrips - Todos los viajes candidatos
   * @returns {Object} { shouldSkip, reason }
   */
  shouldSkipAssignment(photo, allTrips) {
    // Si no tiene coordenadas ni país, no se puede asignar
    if (!photo.latitude && !photo.longitude && !photo.country) {
      return { shouldSkip: true, reason: 'Sin datos de ubicación' };
    }
    
    // Si no tiene fecha, no se puede asignar temporalmente
    if (!photo.bestDate) {
      return { shouldSkip: true, reason: 'Sin fecha' };
    }
    
    // Evaluar contra todos los viajes
    const evaluations = allTrips.map(trip => 
      this.evaluatePhoto(photo, trip, [], null)
    );
    
    // Si todos los scores son bajos, es ambigua
    const maxConfidence = Math.max(...evaluations.map(e => e.confidence));
    
    if (maxConfidence < this.thresholds.HITL_VERIFY) {
      return { shouldSkip: true, reason: 'Baja confianza contra todos los viajes' };
    }
    
    return { shouldSkip: false };
  }

  getWeights() {
    return { ...this.weights };
  }

  getThresholds() {
    return { ...this.thresholds };
  }
}

export default new ConsensusEngine();