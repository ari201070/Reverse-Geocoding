/**
 * BookingDocumentParser - Parser de documentos de viaje
 * Escanea F:\Documentos_Viaje\ y G:\ para encontrar documentos de reserva
 * y extraer información de viajes (fechas, países, ciudades)
 */

import fs from "fs";
import path from "path";

// Estructura de un viaje extraído de documentos
const TRIP_TEMPLATE = {
  id: '',
  name: '',
  type: 'international', // 'international' | 'local' | 'activity'
  country: '',
  cities: [],
  startDate: null,
  endDate: null,
  documents: [],
  bookingReferences: [],
  source: 'booking_document',
};

// Patrones de archivos de documentos de viaje
const TRAVEL_DOC_PATTERNS = [
  /booking/i,
  /reservation/i,
  /confirmación/i,
  /confirmacion/i,
  /ticket/i,
  /itinerary/i,
  /itinerario/i,
  /boarding/i,
  /flight/i,
  /vuelo/i,
  /hotel/i,
  /polisa/i,
  /seguro/i,
  /insurance/i,
];

// Patrones para extraer fechas de nombres de archivos
const DATE_PATTERNS = [
  /(\d{4})-(\d{2})-(\d{2})/,  // YYYY-MM-DD
  /(\d{2})[/-](\d{2})[/-](\d{4})/,  // DD-MM-YYYY
  /(\d{4})(\d{2})(\d{2})/,  // YYYYMMDD
];

// Mapeo de carpetas de meses en español
const MONTH_MAP = {
  'Enero': 0, 'Febrero': 1, 'Marzo': 2, 'Abril': 3,
  'Mayo': 4, 'Junio': 5, 'Julio': 6, 'Agosto': 7,
  'Septiembre': 8, 'Octubre': 9, 'Noviembre': 10, 'Diciembre': 11,
};

// Mapeo de carpetas de meses en hebreo
const MONTH_MAP_HEBREW = {
  'ינואר': 0, 'פברואר': 1, 'מרץ': 2, 'אפריל': 3,
  'מאי': 4, 'יוני': 5, 'יולי': 6, 'אוגוסט': 7,
  'ספטמבר': 8, 'אוקטובר': 9, 'נובמבר': 10, 'דצמבר': 11,
};

export class BookingDocumentParser {
  constructor() {
    this.trips = new Map();
    this.documents = [];
  }

  /**
   * Escanea los directorios de documentos de viaje
   * @param {string[]} directories - Directorios a escanear
   * @returns {Object[]} Lista de viajes extraídos
   */
  async scanDirectories(directories) {
    console.error("🔍 Escaneando directorios de documentos de viaje...");
    
    for (const dir of directories) {
      if (!fs.existsSync(dir)) {
        console.error(`⚠️ Directorio no encontrado: ${dir}`);
        continue;
      }
      
      await this._scanDirectory(dir, 0);
    }
    
    console.error(`📄 Documentos encontrados: ${this.documents.length}`);
    console.error(`🧳 Viajes identificados: ${this.trips.size}`);
    
    return Array.from(this.trips.values());
  }

  /**
   * Escanea un directorio recursivamente
   */
  async _scanDirectory(dirPath, depth) {
    if (depth > 5) return; // Limitar profundidad
    
    try {
      const entries = fs.readdirSync(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        
        if (entry.isDirectory()) {
          await this._scanDirectory(fullPath, depth + 1);
        } else if (entry.isFile()) {
          this._processFile(fullPath, dirPath);
        }
      }
    } catch (error) {
      console.error(`Error escaneando ${dirPath}: ${error.message}`);
    }
  }

  /**
   * Procesa un archivo individual
   */
  _processFile(filePath, parentDir) {
    const fileName = path.basename(filePath);
    const ext = path.extname(fileName).toLowerCase();
    
    // Solo procesar archivos de documentos de viaje
    const isTravelDoc = TRAVEL_DOC_PATTERNS.some(pattern => pattern.test(fileName));
    if (!isTravelDoc) return;
    
    // Extraer información del archivo
    const docInfo = {
      path: filePath,
      name: fileName,
      extension: ext,
      parentDir: parentDir,
      tripId: this._extractTripId(parentDir),
      dates: this._extractDatesFromPath(filePath),
      country: this._extractCountryFromPath(filePath),
      city: this._extractCityFromPath(filePath),
    };
    
    this.documents.push(docInfo);
    
    // Crear o actualizar viaje
    this._createOrUpdateTrip(docInfo);
  }

  /**
   * Extrae el ID del viaje desde la ruta del directorio
   */
  _extractTripId(dirPath) {
    // Buscar patrones como "2025/Septiembre" o "2023/Mayo"
    const yearMatch = dirPath.match(/(\d{4})/);
    const monthMatch = dirPath.match(/(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)/i);
    
    if (yearMatch) {
      const year = yearMatch[1];
      const month = monthMatch ? monthMatch[1] : 'Unknown';
      return `${year}-${month}`;
    }
    
    return null;
  }

  /**
   * Extrae fechas desde la ruta del archivo
   */
  _extractDatesFromPath(filePath) {
    const dates = [];
    
    // Buscar fechas en la ruta
    for (const pattern of DATE_PATTERNS) {
      const matches = filePath.matchAll(new RegExp(pattern.source, 'g'));
      for (const match of matches) {
        try {
          let date;
          if (pattern.source.includes('(\\d{4})-(\\d{2})-(\\d{2})')) {
            date = new Date(match[1], match[2] - 1, match[3]);
          } else if (pattern.source.includes('(\\d{2})[/-](\\d{2})[/-](\\d{4})')) {
            date = new Date(match[3], match[2] - 1, match[1]);
          } else if (pattern.source.includes('(\\d{4})(\\d{2})(\\d{2})')) {
            date = new Date(match[1], match[2] - 1, match[3]);
          }
          
          if (date && !isNaN(date.getTime())) {
            dates.push(date);
          }
        } catch (e) {
          // Ignorar fechas inválidas
        }
      }
    }
    
    // Buscar meses en español/hebreo en la ruta
    const monthNames = [...Object.keys(MONTH_MAP), ...Object.keys(MONTH_MAP_HEBREW)];
    for (const monthName of monthNames) {
      if (filePath.toLowerCase().includes(monthName.toLowerCase())) {
        // El mes está en la ruta, pero necesitamos el año
        const yearMatch = filePath.match(/(\d{4})/);
        if (yearMatch) {
          const monthNum = MONTH_MAP[monthName] ?? MONTH_MAP_HEBREW[monthName];
          if (monthNum !== undefined) {
            // Usar el primer día del mes como fecha aproximada
            dates.push(new Date(yearMatch[1], monthNum, 1));
          }
        }
      }
    }
    
    return dates;
  }

  /**
   * Extrae el país desde la ruta del archivo
   */
  _extractCountryFromPath(filePath) {
    const countryPatterns = [
      { pattern: /argentin/i, country: 'Argentina' },
      { pattern: /sloven/i, country: 'Slovenia' },
      { pattern: /croati/i, country: 'Croatia' },
      { pattern: /montenegr/i, country: 'Montenegro' },
      { pattern: /bosn/i, country: 'Bosnia and Herzegovina' },
      { pattern: /itali/i, country: 'Italy' },
      { pattern: /greci|crete|kriti/i, country: 'Crete' },
      { pattern: /israel/i, country: 'Israel' },
      { pattern: /denmark|dinamarca/i, country: 'Denmark' },
    ];
    
    for (const { pattern, country } of countryPatterns) {
      if (pattern.test(filePath)) {
        return country;
      }
    }
    
    return null;
  }

  /**
   * Extrae la ciudad desde la ruta del archivo
   */
  _extractCityFromPath(filePath) {
    const cityPatterns = [
      { pattern: /buenos.?aires/i, city: 'Buenos Aires' },
      { pattern: /bariloche/i, city: 'San Carlos de Bariloche' },
      { pattern: /mendoza/i, city: 'Mendoza' },
      { pattern: /rosario/i, city: 'Rosario' },
      { pattern: /salta/i, city: 'Salta' },
      { pattern: /iguaz/i, city: 'Iguazú' },
      { pattern: /bled/i, city: 'Bled' },
      { pattern: /dubrovnik/i, city: 'Dubrovnik' },
      { pattern: /kotor/i, city: 'Kotor' },
      { pattern: /firenze|florence/i, city: 'Florence' },
      { pattern: /pisa/i, city: 'Pisa' },
      { pattern: /rome|roma/i, city: 'Rome' },
      { pattern: /venice|venecia/i, city: 'Venice' },
      { pattern: /sarajevo/i, city: 'Sarajevo' },
    ];
    
    for (const { pattern, city } of cityPatterns) {
      if (pattern.test(filePath)) {
        return city;
      }
    }
    
    return null;
  }

  /**
   * Crea o actualiza un viaje basándose en la información del documento
   */
  _createOrUpdateTrip(docInfo) {
    const tripId = docInfo.tripId || `trip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    if (!this.trips.has(tripId)) {
      this.trips.set(tripId, {
        ...TRIP_TEMPLATE,
        id: tripId,
        name: this._generateTripName(docInfo),
        country: docInfo.country || 'Unknown',
        documents: [],
      });
    }
    
    const trip = this.trips.get(tripId);
    
    // Agregar documento
    trip.documents.push(docInfo);
    
    // Actualizar fechas si es necesario
    if (docInfo.dates.length > 0) {
      const earliest = new Date(Math.min(...docInfo.dates));
      const latest = new Date(Math.max(...docInfo.dates));
      
      if (!trip.startDate || earliest < trip.startDate) {
        trip.startDate = earliest;
      }
      if (!trip.endDate || latest > trip.endDate) {
        trip.endDate = latest;
      }
    }
    
    // Actualizar país si es necesario
    if (docInfo.country && !trip.country) {
      trip.country = docInfo.country;
    }
    
    // Agregar ciudad si es nueva
    if (docInfo.city && !trip.cities.includes(docInfo.city)) {
      trip.cities.push(docInfo.city);
    }
  }

  /**
   * Genera un nombre para el viaje
   */
  _generateTripName(docInfo) {
    const year = docInfo.dates.length > 0 
      ? docInfo.dates[0].getFullYear() 
      : new Date().getFullYear();
    
    const country = docInfo.country || 'Unknown';
    
    return `${country} ${year}`;
  }

  /**
   * Obtiene todos los viajes encontrados
   */
  getTrips() {
    return Array.from(this.trips.values());
  }

  /**
   * Obtiene todos los documentos encontrados
   */
  getDocuments() {
    return this.documents;
  }
}

export default BookingDocumentParser;