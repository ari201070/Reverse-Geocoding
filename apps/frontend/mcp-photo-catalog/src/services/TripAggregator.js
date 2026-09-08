/**
 * TripAggregator - Lógica central de agrupación de fotos en viajes
 * 
 * Implementa el flujo del Arquitecto:
 * 1. Ingesta de documentos de viaje (fuente de verdad)
 * 2. Enriquecimiento espacial (H3 + SpatialCache)
 * 3. Asignación de fotos a viajes (documento-primero)
 * 4. Creación de visitas locales para fotos no asignadas
 * 5. Validación por consenso (Antigravity 2.0)
 */

import h3Service from "./H3Service.js";
import spatialCache from "./SpatialCacheClient.js";
import countryNormalizer from "./CountryNormalizer.js";
import consensusEngine from "./ConsensusEngine.js";
import PhotoRepository from "./PhotoRepository.js";
import { KNOWN_TRIPS, getTripByDate } from "./KnownTrips.js";

// Instancia del repositorio de fotos
const photoRepository = new PhotoRepository('C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db');

// Configuración por defecto
const DEFAULT_CONFIG = {
  mergeWindowDays: 7,        // Ventana para fusionar países en un viaje
  minPhotosPerDay: 1,        // Mínimo de fotos para crear actividad
  maxH3Distance: 2,           // Distancia máxima H3 para fotos cercanas
  clusterTimeWindow: 5 * 60 * 1000, // 5 minutos para cluster temporal
  localActivityDays: 3,      // Días máximos para considerar "actividad local"
  documentDirectories: [
    'F:\\Documentos_Viaje',
    'G:\\האחסון שלי',
  ],
};

// Países que se consideran "internacionales" para el usuario (Argentina/Israel)
const INTERNATIONAL_COUNTRIES = [
  'Argentina', 'Slovenia', 'Croatia', 'Montenegro', 'Bosnia and Herzegovina',
  'Italy', 'Crete', 'Greece', 'Denmark', 'Spain', 'France', 'Germany',
  'Portugal', 'Netherlands', 'Belgium', 'Switzerland', 'Austria',
  'Czech Republic', 'Hungary', 'Poland', 'Norway', 'Sweden', 'Finland',
  'Iceland', 'Ireland', 'United Kingdom', 'Turkey', 'Egypt', 'Morocco',
];

// Países que se consideran "locales" (Israel)
const LOCAL_COUNTRIES = ['Israel'];

export class TripAggregator {
  constructor(config = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.photos = [];
    this.trips = [];
    this.activities = [];
    this.unassigned = [];
  }

  /**
   * Ejecuta el flujo completo de agregación
   * @param {Object} options - Opciones de procesamiento
   * @returns {Object} { trips, activities, unassigned, stats }
   */
  async process(options = {}) {
    const startTime = Date.now();
    console.error("🚀 Iniciando agregación de viajes (versión documento-primero)...");
    
    // 1. Usar viajes conocidos desde documentos (fuente de verdad)
    this.trips = KNOWN_TRIPS.map(trip => ({
      ...trip,
      h3Indices: [],
      activities: [],
      totalPhotos: 0,
      source: 'booking_document',
    }));
    console.error(`📄 Viajes conocidos desde documentos: ${this.trips.length}`);
    
    // 2. Cargar fotos
    this.photos = photoRepository.getPhotosWithLocation({
      minYear: options.minYear || 2002,
      maxYear: options.maxYear || 2030,
    });
    console.error(`📸 Fotos cargadas: ${this.photos.length}`);
    
    // 3. Enriquecer con H3 y normalización
    const enrichedPhotos = this._enrichPhotos();
    console.error(`🗺️  Fotos enriquecidas con H3: ${enrichedPhotos.filter(p => p.h3Index).length}`);
    
    // 4. Asignar fotos a viajes existentes (documento-primero)
    this._assignPhotosToTrips(enrichedPhotos);
    
    // 5. Crear micro-actividades para fotos no asignadas
    const unassignedPhotos = enrichedPhotos.filter(p => !p.tripId);
    const microActivities = this._createMicroActivities(unassignedPhotos);
    console.error(`📍 Micro-actividades creadas: ${microActivities.length}`);
    
    // 6. Detectar viajes locales/actividades desde fotos
    const localTrips = this._detectLocalTrips(microActivities);
    this.trips.push(...localTrips);
    console.error(`🏠 Viajes locales/actividades: ${localTrips.length}`);
    
    // 7. Generar actividades finales
    this.activities = this._createActivities(microActivities);
    console.error(`🎯 Actividades generadas: ${this.activities.length}`);
    
    // 8. Identificar fotos no asignadas
    this.unassigned = enrichedPhotos.filter(p => !p.tripId);
    console.error(`❓ Fotos no asignadas: ${this.unassigned.length}`);
    
    const endTime = Date.now();
    const stats = {
      totalPhotos: this.photos.length,
      enrichedPhotos: enrichedPhotos.length,
      knownTrips: this.trips.filter(t => t.source === 'booking_document').length,
      internationalTrips: this.trips.filter(t => t.type === 'international').length,
      localTrips: this.trips.filter(t => t.type === 'local').length,
      microActivities: microActivities.length,
      trips: this.trips.length,
      activities: this.activities.length,
      unassigned: this.unassigned.length,
      processingTimeMs: endTime - startTime,
      spatialCacheStats: spatialCache.getStats(),
    };
    
    console.error(`✅ Agregación completada en ${stats.processingTimeMs}ms`);
    
    return {
      trips: this.trips,
      activities: this.activities,
      unassigned: this.unassigned,
      stats,
    };
  }

  /**
   * Paso 1: Crear viajes desde documentos de booking
   */
  _createTripsFromDocuments(docTrips) {
    return docTrips.map(docTrip => {
      // Determinar si es viaje internacional o local
      const isInternational = INTERNATIONAL_COUNTRIES.includes(docTrip.country);
      const isLocal = LOCAL_COUNTRIES.includes(docTrip.country);
      
      let type = 'international';
      if (isLocal) type = 'local';
      
      return {
        id: docTrip.id,
        name: docTrip.name,
        type: type,
        destination: docTrip.country,
        color: 'indigo',
        countries: [docTrip.country].filter(Boolean),
        cities: docTrip.cities || [],
        startDate: docTrip.startDate ? this._formatDate(docTrip.startDate) : null,
        endDate: docTrip.endDate ? this._formatDate(docTrip.endDate) : null,
        h3Indices: [],
        activities: [],
        totalPhotos: 0,
        documents: docTrip.documents || [],
        source: 'booking_document',
      };
    });
  }

  /**
   * Paso 2: Enriquecer fotos con H3 y normalización de países
   */
  _enrichPhotos() {
    return this.photos.map(photo => {
      const date = photoRepository.getBestDate(photo);
      const country = countryNormalizer.resolveCountry(photo);
      const h3Index = photo.latitude && photo.longitude 
        ? h3Service.latLngToH3(photo.latitude, photo.longitude)
        : null;
      
      // Intentar caché espacial
      let cachedData = null;
      if (photo.latitude && photo.longitude) {
        cachedData = spatialCache.get(photo.latitude, photo.longitude);
      }
      
      // Detectar si la fecha parece ser de subida/actualización
      const dateReliability = this._checkDateReliability(photo, date);
      
      return {
        ...photo,
        bestDate: date,
        dateReliability: dateReliability,
        country: country || cachedData?.country,
        city: photo.city || cachedData?.city,
        h3Index: h3Index || cachedData?.h3Index,
        tripId: null,
        activityId: null,
        confidence: 0,
      };
    });
  }

  /**
   * Verifica la confiabilidad de la fecha de una foto
   */
  _checkDateReliability(photo, date) {
    if (!date) return 'unknown';
    
    const now = new Date();
    const photoYear = date.getFullYear();
    const currentYear = now.getFullYear();
    
    // Si la fecha es futura (>2 años en el futuro), es probablemente incorrecta
    if (photoYear > currentYear + 2) {
      return 'upload_date'; // Probablemente fecha de subida
    }
    
    // Si la fecha es muy reciente (<1 mes) y el archivo es antiguo
    const fileModified = photo.file_path ? new Date(photo.file_path) : null;
    if (fileModified && (now - fileModified) > 365 * 24 * 60 * 60 * 1000) {
      // Archivo antiguo pero fecha reciente
      const daysDiff = (now - date) / (1000 * 60 * 60 * 24);
      if (daysDiff < 30) {
        return 'suspicious'; // Fecha sospechosamente reciente
      }
    }
    
    return 'reliable';
  }

  /**
   * Paso 3: Asignar fotos a viajes existentes (documento-primero)
   */
  _assignPhotosToTrips(enrichedPhotos) {
    for (const photo of enrichedPhotos) {
      if (!photo.bestDate || !photo.country) continue;
      
      const photoDate = this._formatDate(photo.bestDate);
      const photoCountry = photo.country;
      
      // Buscar viaje que coincida usando KnownTrips
      const matchingTrip = getTripByDate(photoDate, photoCountry);
      
      if (matchingTrip) {
        // Encontrar el viaje en this.trips
        const trip = this.trips.find(t => t.id === matchingTrip.id);
        if (trip) {
          photo.tripId = trip.id;
          trip.totalPhotos++;
          
          // Agregar H3 al viaje
          if (photo.h3Index && !trip.h3Indices.includes(photo.h3Index)) {
            trip.h3Indices.push(photo.h3Index);
          }
          
          // Agregar ciudad si es nueva
          if (photo.city && !trip.cities.includes(photo.city)) {
            trip.cities.push(photo.city);
          }
        }
      }
    }
  }

  /**
   * Paso 4: Crear micro-actividades agrupadas por H3 + fecha
   */
  _createMicroActivities(enrichedPhotos) {
    // Agrupar por H3 + fecha (día)
    const groups = new Map();
    
    for (const photo of enrichedPhotos) {
      if (!photo.h3Index || !photo.bestDate) continue;
      if (photo.tripId) continue; // Ya asignada a un viaje
      
      const dateKey = this._formatDate(photo.bestDate);
      const groupKey = `${photo.h3Index}|${dateKey}`;
      
      if (!groups.has(groupKey)) {
        groups.set(groupKey, {
          id: `micro-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          h3Index: photo.h3Index,
          date: dateKey,
          country: photo.country,
          city: photo.city,
          photos: [],
          lat: photo.latitude,
          lng: photo.longitude,
        });
      }
      
      groups.get(groupKey).photos.push(photo);
    }
    
    return Array.from(groups.values());
  }

  /**
   * Paso 5: Detectar viajes locales/actividades desde fotos
   */
  _detectLocalTrips(microActivities) {
    if (microActivities.length === 0) return [];
    
    // Agrupar por país y rango temporal
    const countryGroups = new Map();
    
    for (const activity of microActivities) {
      const country = activity.country || 'Unknown';
      if (!countryGroups.has(country)) {
        countryGroups.set(country, []);
      }
      countryGroups.get(country).push(activity);
    }
    
    const localTrips = [];
    
    for (const [country, activities] of countryGroups) {
      // Ordenar por fecha
      activities.sort((a, b) => new Date(a.date) - new Date(b.date));
      
      // Agrupar en ventanas temporales
      let currentGroup = [activities[0]];
      
      for (let i = 1; i < activities.length; i++) {
        const prevDate = new Date(currentGroup[currentGroup.length - 1].date);
        const currDate = new Date(activities[i].date);
        const daysDiff = (currDate - prevDate) / (1000 * 60 * 60 * 24);
        
        if (daysDiff <= this.config.localActivityDays) {
          currentGroup.push(activities[i]);
        } else {
          // Crear viaje local para el grupo actual
          if (currentGroup.length >= 2) {
            localTrips.push(this._createLocalTrip(country, currentGroup));
          }
          currentGroup = [activities[i]];
        }
      }
      
      // Procesar último grupo
      if (currentGroup.length >= 2) {
        localTrips.push(this._createLocalTrip(country, currentGroup));
      }
    }
    
    return localTrips;
  }

  /**
   * Crea un viaje local/actividad
   */
  _createLocalTrip(country, activities) {
    const dates = activities.map(a => a.date).sort();
    const cities = [...new Set(activities.map(a => a.city).filter(Boolean))];
    const h3Indices = [...new Set(activities.map(a => a.h3Index).filter(Boolean))];
    
    // Determinar si es Israel (local) u otro país
    const isLocal = LOCAL_COUNTRIES.includes(country);
    
    return {
      id: `local-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: `${country} ${new Date(dates[0]).getFullYear()} - Actividad`,
      type: isLocal ? 'local' : 'activity',
      destination: country,
      color: isLocal ? 'gray' : 'green',
      countries: [country],
      cities: cities,
      startDate: dates[0],
      endDate: dates[dates.length - 1],
      h3Indices: h3Indices,
      activities: [],
      totalPhotos: activities.reduce((sum, a) => sum + a.photos.length, 0),
      documents: [],
      source: 'photo_clustering',
    };
  }

  /**
   * Paso 6: Crear actividades finales para el viaje
   */
  _createActivities(microActivities) {
    const activities = [];
    
    for (const micro of microActivities) {
      if (micro.photos.length < this.config.minPhotosPerDay) continue;
      
      // Buscar la photo representativa (con GPS, o primera)
      const repPhoto = micro.photos.find(p => p.latitude && p.longitude) || micro.photos[0];
      
      // Buscar el viaje al que pertenece
      const tripId = this._findTripForPhoto(repPhoto);
      
      const activity = {
        id: `activity-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        fileName: `${micro.photos.length} fotos - ${micro.date}`,
        mimeType: 'application/vnd.photo-group',
        isTravelDocument: true,
        category: 'activity',
        supplier: 'Fotos personales',
        title: `Día en ${micro.country || 'Lugar desconocido'}`,
        startDate: micro.date,
        startTime: micro.photos[0].bestDate?.toTimeString().slice(0, 5) || '',
        endDate: micro.date,
        endTime: micro.photos[micro.photos.length - 1].bestDate?.toTimeString().slice(0, 5) || '',
        confirmationNumber: `PHOTO-${(micro.country || 'UNK').substring(0, 3).toUpperCase()}-${micro.date.replace(/-/g, '')}`,
        location: this._buildLocation(repPhoto),
        passengerOrGuestName: 'Fotos de viaje',
        price: 0,
        currency: 'EUR',
        details: `${micro.photos.length} fotos tomadas el ${micro.date} en ${micro.country || 'lugar desconocido'}. Primera: ${repPhoto.filename}`,
        summary: `Actividad generada desde ${micro.photos.length} fotos en ${micro.country || 'lugar desconocido'}`,
        iconLink: '',
        tripId: tripId,
        _photoIds: micro.photos.map(p => p.id),
        _photoPaths: micro.photos.map(p => p.file_path),
        _representativePhoto: repPhoto.id,
        _country: micro.country,
        _lat: repPhoto.latitude,
        _lng: repPhoto.longitude,
        _h3Index: micro.h3Index,
      };
      
      activities.push(activity);
      
      // Marcar fotos como asignadas
      for (const photo of micro.photos) {
        photo.tripId = tripId;
        photo.activityId = activity.id;
      }
    }
    
    return activities;
  }

  /**
   * Encuentra el viaje al que pertenece una foto
   */
  _findTripForPhoto(photo) {
    // Primero buscar viajes internacionales
    for (const trip of this.trips) {
      if (trip.type === 'international') {
        // Verificar coincidencia de país
        const tripCountries = trip.countries || [trip.country];
        if (photo.country && tripCountries.includes(photo.country)) {
          // Verificar coincidencia temporal
          if (photo.bestDate) {
            const photoDate = this._formatDate(photo.bestDate);
            if (trip.startDate && trip.endDate) {
              if (photoDate >= trip.startDate && photoDate <= trip.endDate) {
                return trip.id;
              }
            }
          }
        }
      }
    }
    
    // Luego buscar viajes locales/actividades
    for (const trip of this.trips) {
      if (trip.type === 'local' || trip.type === 'activity') {
        if (photo.country && trip.countries.includes(photo.country)) {
          if (photo.bestDate) {
            const photoDate = this._formatDate(photo.bestDate);
            if (trip.startDate && trip.endDate) {
              if (photoDate >= trip.startDate && photoDate <= trip.endDate) {
                return trip.id;
              }
            }
          }
        }
      }
    }
    
    return null;
  }

  /**
   * Construye la cadena de ubicación
   */
  _buildLocation(photo) {
    const parts = [];
    if (photo.city) parts.push(photo.city);
    if (photo.location_name) parts.push(photo.location_name);
    if (photo.country) parts.push(photo.country);
    return parts.join(', ') || photo.country || 'Lugar desconocido';
  }

  /**
   * Formatea una fecha a YYYY-MM-DD
   */
  _formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toISOString().split('T')[0];
  }

  getTrips() {
    return this.trips;
  }

  getActivities() {
    return this.activities;
  }

  getUnassigned() {
    return this.unassigned;
  }
}

export default TripAggregator;