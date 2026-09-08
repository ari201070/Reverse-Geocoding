/**
 * PhotoRepository - Capa de acceso a datos de photo_catalog.db
 * Abstrae la lectura de la base de datos de fotos
 */

import Database from "better-sqlite3";

export class PhotoRepository {
  constructor(dbPath) {
    this.dbPath = dbPath;
    this.db = null;
  }

  connect() {
    if (!this.db) {
      this.db = new Database(this.dbPath, { readonly: true });
      this.db.pragma("journal_mode = WAL");
    }
    return this;
  }

  close() {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }

  /**
   * Obtiene todas las fotos con datos de ubicación
   * @param {Object} filters - Filtros opcionales
   * @param {number} filters.minYear - Año mínimo
   * @param {number} filters.maxYear - Año máximo
   * @param {boolean} filters.onlyWithCountry - Solo fotos con país
   * @returns {Array} Fotos con metadatos
   */
  getPhotosWithLocation(filters = {}) {
    this.connect();
    
    let query = `
      SELECT 
        id, file_path, filename, date_taken, date_source,
        latitude, longitude, 
        location_name, location_address, 
        country, city, 
        folder_source, sha256, file_ext
      FROM photos 
      WHERE (latitude IS NOT NULL AND longitude IS NOT NULL)
    `;
    
    const params = [];
    
    if (filters.onlyWithCountry) {
      query += ` AND country IS NOT NULL AND country != ''`;
    }
    
    query += ` ORDER BY date_taken ASC, file_path ASC`;
    
    const photos = this.db.prepare(query).all(...params);
    
    // Filtrar por año si es necesario
    if (filters.minYear || filters.maxYear) {
      return photos.filter(p => {
        const year = this._extractYear(p);
        if (!year) return false;
        if (filters.minYear && year < filters.minYear) return false;
        if (filters.maxYear && year > filters.maxYear) return false;
        return true;
      });
    }
    
    return photos;
  }

  /**
   * Obtiene estadísticas del catálogo
   */
  getStats() {
    this.connect();
    
    const getCount = (query) => {
      const result = this.db.prepare(query).get();
      return result?.count || 0;
    };
    
    return {
      total: getCount("SELECT COUNT(*) as count FROM photos"),
      withGps: getCount("SELECT COUNT(*) as count FROM photos WHERE latitude IS NOT NULL AND longitude IS NOT NULL"),
      withCountry: getCount("SELECT COUNT(*) as count FROM photos WHERE country IS NOT NULL AND country != ''"),
      withDateTaken: getCount("SELECT COUNT(*) as count FROM photos WHERE date_taken IS NOT NULL"),
    };
  }

  /**
   * Extrae el año de una foto (de EXIF o ruta)
   */
  _extractYear(photo) {
    // Intentar de date_taken
    if (photo.date_taken) {
      const match = photo.date_taken.match(/^(\d{4})/);
      if (match) return parseInt(match[1], 10);
    }
    
    // Intentar de file_path (formato: F:\YYYY\Mes\...)
    if (photo.file_path) {
      const match = photo.file_path.match(/[\\/](\d{4})[\\/]/);
      if (match) return parseInt(match[1], 10);
    }
    
    return null;
  }

  /**
   * Extrae la fecha completa de una foto
   */
  getBestDate(photo) {
    // Intentar date_taken
    if (photo.date_taken) {
      // Manejar formato "2013:07:23 17:34:50" (con dos puntos)
      let dateStr = photo.date_taken;
      if (dateStr.includes(':') && !dateStr.includes('-')) {
        // Convertir "2013:07:23" a "2013-07-23"
        dateStr = dateStr.replace(/(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3');
      }
      
      const d = new Date(dateStr);
      if (!isNaN(d.getTime())) return d;
    }
    
    // Intentar file_path
    if (photo.file_path) {
      const yearMatch = photo.file_path.match(/[\\/](\d{4})[\\/]/);
      const monthMap = {
        'Enero': 0, 'Febrero': 1, 'Marzo': 2, 'Abril': 3, 'Mayo': 4, 'Junio': 5,
        'Julio': 6, 'Agosto': 7, 'Septiembre': 8, 'Octubre': 9, 'Noviembre': 10, 'Diciembre': 11,
        'January': 0, 'February': 1, 'March': 2, 'April': 3, 'May': 4, 'June': 5,
        'July': 6, 'August': 7, 'September': 8, 'October': 9, 'November': 10, 'December': 11
      };
      
      const parts = photo.file_path.split(/[\\/]/);
      let month = 0;
      for (const part of parts) {
        if (monthMap[part] !== undefined) {
          month = monthMap[part];
          break;
        }
      }
      
      if (yearMatch) {
        return new Date(parseInt(yearMatch[1], 10), month, 1);
      }
    }
    
    return null;
  }
}

export default PhotoRepository;