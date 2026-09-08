/**
 * CountryNormalizer - Capa de normalización de países y ciudades
 * Maneja múltiples idiomas, códigos ISO y variantes
 */

// Mapa de normalización de países: variantes → nombre canónico en inglés
const COUNTRY_NORMALIZATION = {
  // Hebrew → English
  'ישראל': 'Israel',
  // Italian → English
  'Italia': 'Italy',
  // Slovenian → English
  'Slovenija': 'Slovenia',
  // Greek → English (all photos are in Crete, not mainland Greece)
  'Ελλάς': 'Crete',
  // Croatian → English
  'Hrvatska': 'Croatia',
  // Montenegrin/Serbian → English
  'Crna Gora / Црна Гора': 'Montenegro',
  // ISO codes / valores anómalos
  'ISO: IR': 'Iran',
  // Bosnia → English
  'Bosna i Hercegovina / Босна и Херцеговина': 'Bosnia and Herzegovina',
  // Francés
  'France': 'France',
  'França': 'France',
  // Alemán
  'Deutschland': 'Germany',
  'Allemagne': 'Germany',
  // Portugués
  'Brasil': 'Brazil',
  'Portugal': 'Portugal',
  // Otros
  'Suiza': 'Switzerland',
  'Schweiz': 'Switzerland',
  'Suisse': 'Switzerland',
  'Belgique': 'Belgium',
  'België': 'Belgium',
  'Österreich': 'Austria',
  'Nederland': 'Netherlands',
  'Niederlande': 'Netherlands',
  'Holland': 'Netherlands',
  'UK': 'United Kingdom',
  'GB': 'United Kingdom',
  'USA': 'United States',
  'US': 'United States',
};

// Mapa de ciudades → países (fallback cuando no hay país)
const CITY_TO_COUNTRY = {
  // Grecia/Creta
  'Crete': 'Crete', 'Athens': 'Greece', 'Thessaloniki': 'Greece',
  'Santorini': 'Greece', 'Mykonos': 'Greece',
  'Chersonissos': 'Crete', 'Heraklion': 'Crete', 'Iraklion': 'Crete',
  // Italia
  'Rome': 'Italy', 'Milan': 'Italy', 'Florence': 'Italy', 'Venice': 'Italy',
  'Naples': 'Italy', 'Bologna': 'Italy', 'Turin': 'Italy', 'Palermo': 'Italy',
  'Genoa': 'Italy', 'Catania': 'Italy', 'Verona': 'Italy',
  // España
  'Madrid': 'Spain', 'Barcelona': 'Spain', 'Seville': 'Spain',
  'Valencia': 'Spain', 'Granada': 'Spain', 'Malaga': 'Spain',
  // Francia
  'Paris': 'France', 'Lyon': 'France', 'Marseille': 'France',
  'Nice': 'France', 'Bordeaux': 'France',
  // Alemania
  'Berlin': 'Germany', 'Munich': 'Germany', 'Hamburg': 'Germany',
  'Frankfurt': 'Germany', 'Cologne': 'Germany',
  // Países Bajos
  'Amsterdam': 'Netherlands', 'Rotterdam': 'Netherlands', 'Utrecht': 'Netherlands',
  // Austria
  'Vienna': 'Austria', 'Salzburg': 'Austria', 'Innsbruck': 'Austria',
  // Europa Central/Este
  'Prague': 'Czech Republic', 'Budapest': 'Hungary', 'Warsaw': 'Poland',
  'Krakow': 'Poland', 'Lisbon': 'Portugal', 'Porto': 'Portugal',
  'Dublin': 'Ireland', 'Edinburgh': 'United Kingdom', 'Manchester': 'United Kingdom',
  'London': 'United Kingdom', 'Brussels': 'Belgium', 'Bruges': 'Belgium',
  'Zurich': 'Switzerland', 'Geneva': 'Switzerland', 'Bern': 'Switzerland',
  'Oslo': 'Norway', 'Bergen': 'Norway', 'Stockholm': 'Sweden',
  'Copenhagen': 'Denmark', 'Helsinki': 'Finland', 'Reykjavik': 'Iceland',
  // Turquía
  'Istanbul': 'Turkey', 'Ankara': 'Turkey', 'Cappadocia': 'Turkey', 'Antalya': 'Turkey',
  // Medio Oriente
  'Dubai': 'United Arab Emirates', 'Abu Dhabi': 'United Arab Emirates',
  'Jerusalem': 'Israel', 'Tel Aviv': 'Israel', 'Haifa': 'Israel', 'Eilat': 'Israel',
  'Beirut': 'Lebanon', 'Amman': 'Jordan', 'Petra': 'Jordan',
  // Asia
  'Tokyo': 'Japan', 'Kyoto': 'Japan', 'Osaka': 'Japan',
  'Seoul': 'South Korea', 'Busan': 'South Korea',
  'Beijing': 'China', 'Shanghai': 'China', 'Hong Kong': 'Hong Kong',
  'Singapore': 'Singapore', 'Bangkok': 'Thailand', 'Chiang Mai': 'Thailand',
  'Bali': 'Indonesia', 'Jakarta': 'Indonesia', 'Kuala Lumpur': 'Malaysia',
  'Ho Chi Minh City': 'Vietnam', 'Hanoi': 'Vietnam',
  // Oceanía
  'Sydney': 'Australia', 'Melbourne': 'Australia', 'Brisbane': 'Australia',
  'Auckland': 'New Zealand', 'Wellington': 'New Zealand',
  // América del Norte
  'New York': 'United States', 'Los Angeles': 'United States',
  'San Francisco': 'United States', 'Miami': 'United States',
  'Chicago': 'United States', 'Boston': 'United States',
  'Washington': 'United States', 'Las Vegas': 'United States',
  'Toronto': 'Canada', 'Vancouver': 'Canada', 'Montreal': 'Canada',
  'Mexico City': 'Mexico', 'Cancun': 'Mexico',
  // América del Sur
  'Buenos Aires': 'Argentina', 'Bariloche': 'Argentina', 'Mendoza': 'Argentina',
  'Rosario': 'Argentina', 'Ushuaia': 'Argentina',
  'Santiago': 'Chile', 'Lima': 'Peru', 'Cusco': 'Peru',
  'Bogota': 'Colombia', 'Medellin': 'Colombia',
  'Rio de Janeiro': 'Brazil', 'Sao Paulo': 'Brazil', 'Salvador': 'Brazil',
  'Montevideo': 'Uruguay', 'Asuncion': 'Paraguay', 'La Paz': 'Bolivia',
  'Quito': 'Ecuador', 'Caracas': 'Venezuela',
  // Centroamérica/Caribe
  'Panama City': 'Panama', 'San Jose': 'Costa Rica', 'Havana': 'Cuba',
  'Santo Domingo': 'Dominican Republic', 'San Juan': 'Puerto Rico',
  'Nassau': 'Bahamas', 'Kingston': 'Jamaica',
  // Europa del Este
  'Moscow': 'Russia', 'Saint Petersburg': 'Russia',
  'Kiev': 'Ukraine', 'Lviv': 'Ukraine', 'Odessa': 'Ukraine',
  'Minsk': 'Belarus', 'Vilnius': 'Lithuania', 'Riga': 'Latvia', 'Tallinn': 'Estonia',
  'Bratislava': 'Slovakia', 'Ljubljana': 'Slovenia',
  'Zagreb': 'Croatia', 'Split': 'Croatia', 'Dubrovnik': 'Croatia',
  'Sarajevo': 'Bosnia and Herzegovina', 'Belgrade': 'Serbia',
  'Skopje': 'North Macedonia', 'Tirana': 'Albania', 'Podgorica': 'Montenegro',
  'Sofia': 'Bulgaria', 'Bucharest': 'Romania',
  // África
  'Cairo': 'Egypt', 'Alexandria': 'Egypt',
  'Marrakech': 'Morocco', 'Casablanca': 'Morocco',
  'Cape Town': 'South Africa', 'Johannesburg': 'South Africa',
  'Nairobi': 'Kenya', 'Dar es Salaam': 'Tanzania',
};

export class CountryNormalizer {
  /**
   * Normaliza el nombre de un país a su forma canónica en inglés
   * @param {string} country - Nombre del país (cualquier idioma)
   * @returns {string|null} Nombre normalizado o null
   */
  normalizeCountry(country) {
    if (!country || typeof country !== 'string') return null;
    const trimmed = country.trim();
    if (!trimmed) return null;
    return COUNTRY_NORMALIZATION[trimmed] || trimmed;
  }

  /**
   * Obtiene el país a partir de una ciudad
   * @param {string} city - Nombre de la ciudad
   * @returns {string|null} País inferido o null
   */
  getCountryFromCity(city) {
    if (!city || typeof city !== 'string') return null;
    return CITY_TO_COUNTRY[city.trim()] || null;
  }

  /**
   * Resuelve el país de una foto usando país, ciudad y coordenadas
   * @param {Object} photo - Objeto foto con country, city, latitude, longitude
   * @returns {string|null} País resuelto
   */
  resolveCountry(photo) {
    // 1. Intentar normalizar el país existente
    if (photo.country) {
      const normalized = this.normalizeCountry(photo.country);
      if (normalized) return normalized;
    }
    
    // 2. Intentar inferir desde la ciudad
    if (photo.city) {
      const inferred = this.getCountryFromCity(photo.city);
      if (inferred) return inferred;
    }
    
    return null;
  }
}

export default new CountryNormalizer();