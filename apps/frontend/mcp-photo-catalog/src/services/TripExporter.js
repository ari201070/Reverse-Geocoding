/**
 * TripExporter - Capa de salida para viajes y actividades
 * Genera JSON compatible con localStorage de la app
 */

import fs from "fs";
import path from "path";

export class TripExporter {
  constructor(outputDir) {
    this.outputDir = outputDir;
    this._ensureOutputDir();
  }

  /**
   * Asegura que el directorio de salida exista
   */
  _ensureOutputDir() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  /**
   * Exporta viajes y actividades a JSON
   * @param {Object} data - { trips, activities, stats }
   * @returns {Object} { tripsFile, bookingsFile, summaryFile }
   */
  export(data) {
    const { trips, activities, stats } = data;
    const timestamp = Date.now();
    
    // 1. Archivo completo (para revisión)
    const fullOutput = {
      trips,
      activities,
      generatedAt: new Date().toISOString(),
      stats,
    };
    
    const fullPath = path.join(this.outputDir, `photo-trips-${timestamp}.json`);
    fs.writeFileSync(fullPath, JSON.stringify(fullOutput, null, 2));
    
    // 2. Archivo para localStorage (solo actividades)
    const bookingsForStorage = activities.map(a => ({
      ...a,
      webViewLink: a._photoPaths?.[0] ? `file://${a._photoPaths[0].replace(/\\/g, '/')}` : '',
      baseUrl: 'local-photos',
    }));
    
    const bookingsPath = path.join(this.outputDir, `travel_bookings_import_${timestamp}.json`);
    fs.writeFileSync(bookingsPath, JSON.stringify(bookingsForStorage, null, 2));
    
    // 3. Resumen legible
    const summaryPath = path.join(this.outputDir, `trip-summary-${timestamp}.txt`);
    const summary = this._generateSummary(trips, activities, stats);
    fs.writeFileSync(summaryPath, summary);
    
    return {
      tripsFile: fullPath,
      bookingsFile: bookingsPath,
      summaryFile: summaryPath,
    };
  }

  /**
   * Genera un resumen legible de los viajes
   */
  _generateSummary(trips, activities, stats) {
    let summary = '=== RESUMEN DE VIAJES ===\n\n';
    summary += `Generado: ${new Date().toISOString()}\n`;
    summary += `Total fotos procesadas: ${stats.totalPhotos}\n`;
    summary += `Fotos enriquecidas: ${stats.enrichedPhotos}\n`;
    summary += `Micro-actividades: ${stats.microActivities}\n`;
    summary += `Viajes detectados: ${stats.trips}\n`;
    summary += `Actividades generadas: ${stats.activities}\n`;
    summary += `Fotos no asignadas: ${stats.unassigned}\n`;
    summary += `Tiempo de procesamiento: ${stats.processingTimeMs}ms\n`;
    summary += `Caché espacial: ${stats.spatialCacheStats.hitRate} hits\n\n`;
    
    summary += '--- VIAJES ---\n\n';
    
    for (const trip of trips) {
      const tripActivities = activities.filter(a => a.tripId === trip.id);
      summary += `${trip.name}\n`;
      summary += `  Fechas: ${trip.startDate} - ${trip.endDate}\n`;
      summary += `  Países: ${(trip.countries || [trip.country]).join(', ')}\n`;
      summary += `  Actividades: ${tripActivities.length}\n`;
      summary += `  Total fotos: ${trip.totalPhotos}\n\n`;
    }
    
    if (stats.unassigned > 0) {
      summary += '--- FOTOS NO ASIGNADAS ---\n';
      summary += `${stats.unassigned} fotos no pudieron ser asignadas a ningún viaje.\n`;
    }
    
    return summary;
  }

  /**
   * Exporta solo las actividades para importar a localStorage
   */
  exportBookings(activities) {
    const timestamp = Date.now();
    const bookingsForStorage = activities.map(a => ({
      ...a,
      webViewLink: a._photoPaths?.[0] ? `file://${a._photoPaths[0].replace(/\\/g, '/')}` : '',
      baseUrl: 'local-photos',
    }));
    
    const bookingsPath = path.join(this.outputDir, `travel_bookings_import_${timestamp}.json`);
    fs.writeFileSync(bookingsPath, JSON.stringify(bookingsForStorage, null, 2));
    
    return bookingsPath;
  }
}

export default TripExporter;