#!/usr/bin/env node
/**
 * Import photos from photo_catalog.db as "activity" bookings grouped into trips
 * - Groups by country (from country field or city field)
 * - Merges consecutive countries within a time window as same trip
 * - Creates one activity per day per country with photo links
 * - Writes to localStorage-compatible JSON (reversible)
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const OUTPUT_DIR = path.join(__dirname, '..', 'photo-import-output');

// ============ CONFIGURATION ============
const MERGE_WINDOW_DAYS = 7;        // max gap between countries to consider same trip
const MIN_PHOTOS_PER_DAY = 1;       // min photos to create an activity entry
const MIN_YEAR = 2002;              // desde 2002 (fotos más antiguas)
const MAX_YEAR = 2030;              // hasta 2030
// =======================================

// Country name normalization: map variants to canonical English names
const COUNTRY_NORMALIZATION = {
  // Hebrew -> English
  'ישראל': 'Israel',
  // Italian -> English
  'Italia': 'Italy',
  // Slovenian -> English
  'Slovenija': 'Slovenia',
  // Greek -> English
  'Ελλάς': 'Greece',
  // Croatian -> English
  'Hrvatska': 'Croatia',
  // Montenegrin/Serbian -> English
  'Crna Gora / Црна Гора': 'Montenegro',
  // ISO codes / weird ones
  'ISO: IR': 'Iran',
  // Bosnia -> English
  'Bosna i Hercegovina / Босна и Херцеговина': 'Bosnia and Herzegovina',
  // Add more as needed
};

function normalizeCountry(country) {
  if (!country) return null;
  // Trim leading/trailing whitespace and normalize
  const trimmed = country.trim();
  return COUNTRY_NORMALIZATION[trimmed] || trimmed;
}

function normalizeCountry(country) {
  if (!country) return null;
  const trimmed = country.trim();
  return COUNTRY_NORMALIZATION[trimmed] || trimmed;
}

// Country normalization map (city -> country)
const CITY_TO_COUNTRY = {
  'Crete': 'Greece',
  'Athens': 'Greece',
  'Thessaloniki': 'Greece',
  'Santorini': 'Greece',
  'Mykonos': 'Greece',
  'Rome': 'Italy',
  'Milan': 'Italy',
  'Florence': 'Italy',
  'Venice': 'Italy',
  'Naples': 'Italy',
  'Bologna': 'Italy',
  'Turin': 'Italy',
  'Palermo': 'Italy',
  'Genoa': 'Italy',
  'Catania': 'Italy',
  'Verona': 'Italy',
  'Madrid': 'Spain',
  'Barcelona': 'Spain',
  'Seville': 'Spain',
  'Valencia': 'Spain',
  'Granada': 'Spain',
  'Malaga': 'Spain',
  'Paris': 'France',
  'Lyon': 'France',
  'Marseille': 'France',
  'Nice': 'France',
  'Bordeaux': 'France',
  'Berlin': 'Germany',
  'Munich': 'Germany',
  'Hamburg': 'Germany',
  'Frankfurt': 'Germany',
  'Cologne': 'Germany',
  'Amsterdam': 'Netherlands',
  'Rotterdam': 'Netherlands',
  'Utrecht': 'Netherlands',
  'Vienna': 'Austria',
  'Salzburg': 'Austria',
  'Innsbruck': 'Austria',
  'Prague': 'Czech Republic',
  'Budapest': 'Hungary',
  'Warsaw': 'Poland',
  'Krakow': 'Poland',
  'Lisbon': 'Portugal',
  'Porto': 'Portugal',
  'Dublin': 'Ireland',
  'London': 'United Kingdom',
  'Edinburgh': 'United Kingdom',
  'Manchester': 'United Kingdom',
  'Brussels': 'Belgium',
  'Bruges': 'Belgium',
  'Zurich': 'Switzerland',
  'Geneva': 'Switzerland',
  'Bern': 'Switzerland',
  'Oslo': 'Norway',
  'Bergen': 'Norway',
  'Stockholm': 'Sweden',
  'Copenhagen': 'Denmark',
  'Helsinki': 'Finland',
  'Reykjavik': 'Iceland',
  'Athens': 'Greece',
  'Thessaloniki': 'Greece',
  'Istanbul': 'Turkey',
  'Ankara': 'Turkey',
  'Cappadocia': 'Turkey',
  'Antalya': 'Turkey',
  'Dubai': 'United Arab Emirates',
  'Abu Dhabi': 'United Arab Emirates',
  'Tokyo': 'Japan',
  'Kyoto': 'Japan',
  'Osaka': 'Japan',
  'Seoul': 'South Korea',
  'Busan': 'South Korea',
  'Beijing': 'China',
  'Shanghai': 'China',
  'Hong Kong': 'Hong Kong',
  'Singapore': 'Singapore',
  'Bangkok': 'Thailand',
  'Chiang Mai': 'Thailand',
  'Phuket': 'Thailand',
  'Bali': 'Indonesia',
  'Jakarta': 'Indonesia',
  'Kuala Lumpur': 'Malaysia',
  'Ho Chi Minh City': 'Vietnam',
  'Hanoi': 'Vietnam',
  'Sydney': 'Australia',
  'Melbourne': 'Australia',
  'Brisbane': 'Australia',
  'Auckland': 'New Zealand',
  'Wellington': 'New Zealand',
  'New York': 'United States',
  'Los Angeles': 'United States',
  'San Francisco': 'United States',
  'Miami': 'United States',
  'Chicago': 'United States',
  'Boston': 'United States',
  'Washington': 'United States',
  'Las Vegas': 'United States',
  'Toronto': 'Canada',
  'Vancouver': 'Canada',
  'Montreal': 'Canada',
  'Mexico City': 'Mexico',
  'Cancun': 'Mexico',
  'Buenos Aires': 'Argentina',
  'Bariloche': 'Argentina',
  'Mendoza': 'Argentina',
  'Santiago': 'Chile',
  'Lima': 'Peru',
  'Cusco': 'Peru',
  'Bogota': 'Colombia',
  'Medellin': 'Colombia',
  'Rio de Janeiro': 'Brazil',
  'Sao Paulo': 'Brazil',
  'Salvador': 'Brazil',
  'Montevideo': 'Uruguay',
  'Asuncion': 'Paraguay',
  'La Paz': 'Bolivia',
  'Quito': 'Ecuador',
  'Guayaquil': 'Ecuador',
  'Caracas': 'Venezuela',
  'Panama City': 'Panama',
  'San Jose': 'Costa Rica',
  'Managua': 'Nicaragua',
  'Tegucigalpa': 'Honduras',
  'San Salvador': 'El Salvador',
  'Guatemala City': 'Guatemala',
  'Havana': 'Cuba',
  'Santo Domingo': 'Dominican Republic',
  'San Juan': 'Puerto Rico',
  'Nassau': 'Bahamas',
  'Kingston': 'Jamaica',
  'Port of Spain': 'Trinidad and Tobago',
  'Bridgetown': 'Barbados',
  'Castries': 'Saint Lucia',
  'St. George': 'Grenada',
  'Kingstown': 'Saint Vincent and the Grenadines',
  'Roseau': 'Dominica',
  'St. Johns': 'Antigua and Barbuda',
  'Basseterre': 'Saint Kitts and Nevis',
  'The Valley': 'Anguilla',
  'Road Town': 'British Virgin Islands',
  'Charlotte Amalie': 'US Virgin Islands',
  'Philipsburg': 'Sint Maarten',
  'Marigot': 'Saint Martin',
  'Gustavia': 'Saint Barthélemy',
  'Oranjestad': 'Aruba',
  'Willemstad': 'Curaçao',
  'Kralendijk': 'Bonaire',
  "Be'er Ora": 'Israel',
  'Jerusalem': 'Israel',
  'Tel Aviv': 'Israel',
  'Haifa': 'Israel',
  'Eilat': 'Israel',
  'Amman': 'Jordan',
  'Petra': 'Jordan',
  'Aqaba': 'Jordan',
  'Beirut': 'Lebanon',
  'Damascus': 'Syria',
  'Baghdad': 'Iraq',
  'Tehran': 'Iran',
  'Riyadh': 'Saudi Arabia',
  'Jeddah': 'Saudi Arabia',
  'Mecca': 'Saudi Arabia',
  'Medina': 'Saudi Arabia',
  'Doha': 'Qatar',
  'Kuwait City': 'Kuwait',
  'Manama': 'Bahrain',
  'Muscat': 'Oman',
  'Sanaa': 'Yemen',
  'Aden': 'Yemen',
  'Tripoli': 'Libya',
  'Benghazi': 'Libya',
  'Tunis': 'Tunisia',
  'Algiers': 'Algeria',
  'Casablanca': 'Morocco',
  'Marrakech': 'Morocco',
  'Fez': 'Morocco',
  'Rabat': 'Morocco',
  'Tangier': 'Morocco',
  'Cairo': 'Egypt',
  'Alexandria': 'Egypt',
  'Luxor': 'Egypt',
  'Aswan': 'Egypt',
  'Khartoum': 'Sudan',
  'Addis Ababa': 'Ethiopia',
  'Nairobi': 'Kenya',
  'Dar es Salaam': 'Tanzania',
  'Kampala': 'Uganda',
  'Kigali': 'Rwanda',
  'Kinshasa': 'Democratic Republic of the Congo',
  'Lubumbashi': 'Democratic Republic of the Congo',
  'Luanda': 'Angola',
  'Maputo': 'Mozambique',
  'Harare': 'Zimbabwe',
  'Lusaka': 'Zambia',
  'Gaborone': 'Botswana',
  'Windhoek': 'Namibia',
  'Cape Town': 'South Africa',
  'Johannesburg': 'South Africa',
  'Durban': 'South Africa',
  'Pretoria': 'South Africa',
  'Antananarivo': 'Madagascar',
  'Port Louis': 'Mauritius',
  'Victoria': 'Seychelles',
  'Moroni': 'Comoros',
  'Mamoudzou': 'Mayotte',
  'Saint-Denis': 'Réunion',
  'Flic en Flac': 'Mauritius',
  'Grand Baie': 'Mauritius',
  'Malé': 'Maldives',
  'Colombo': 'Sri Lanka',
  'Kandy': 'Sri Lanka',
  'Male': 'Maldives',
  'Dhaka': 'Bangladesh',
  'Kathmandu': 'Nepal',
  'Thimphu': 'Bhutan',
  'Ulaanbaatar': 'Mongolia',
  'Astana': 'Kazakhstan',
  'Almaty': 'Kazakhstan',
  'Bishkek': 'Kyrgyzstan',
  'Dushanbe': 'Tajikistan',
  'Ashgabat': 'Turkmenistan',
  'Tashkent': 'Uzbekistan',
  'Yerevan': 'Armenia',
  'Tbilisi': 'Georgia',
  'Baku': 'Azerbaijan',
  'Moscow': 'Russia',
  'Saint Petersburg': 'Russia',
  'Novosibirsk': 'Russia',
  'Yekaterinburg': 'Russia',
  'Vladivostok': 'Russia',
  'Kiev': 'Ukraine',
  'Lviv': 'Ukraine',
  'Odessa': 'Ukraine',
  'Minsk': 'Belarus',
  'Vilnius': 'Lithuania',
  'Riga': 'Latvia',
  'Tallinn': 'Estonia',
  'Helsinki': 'Finland',
  'Warsaw': 'Poland',
  'Bratislava': 'Slovakia',
  'Ljubljana': 'Slovenia',
  'Zagreb': 'Croatia',
  'Split': 'Croatia',
  'Dubrovnik': 'Croatia',
  'Sarajevo': 'Bosnia and Herzegovina',
  'Belgrade': 'Serbia',
  'Skopje': 'North Macedonia',
  'Tirana': 'Albania',
  'Podgorica': 'Montenegro',
  'Pristina': 'Kosovo',
  'Sofia': 'Bulgaria',
  'Bucharest': 'Romania',
  'Cluj-Napoca': 'Romania',
  'Chisinau': 'Moldova',
};

function getCountryFromCity(city) {
  if (!city) return null;
  return CITY_TO_COUNTRY[city] || null;
}

function extractDateFromPath(filePath) {
  // Path format: F:\YYYY\Mes\filename
  const match = filePath.match(/[\\/](\d{4})[\\/]/);
  if (match) return parseInt(match[1], 10);
  return null;
}

function extractMonthFromPath(filePath) {
  const monthMap = {
    'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
    'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12,
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
  };
  const parts = filePath.split(/[\\/]/);
  for (const part of parts) {
    if (monthMap[part]) return monthMap[part];
  }
  return null;
}

function parseDateTaken(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? null : d;
}

function getBestDate(photo) {
  // Priority: EXIF date_taken > folder path year/month > null
  if (photo.date_taken) {
    const d = parseDateTaken(photo.date_taken);
    if (d) return d;
  }
  const year = extractDateFromPath(photo.file_path);
  const month = extractMonthFromPath(photo.file_path);
  if (year) {
    return new Date(year, (month || 1) - 1, 1);
  }
  return null;
}

function getCountry(photo) {
  if (photo.country && photo.country.trim()) return normalizeCountry(photo.country.trim());
  if (photo.city) {
    const inferred = getCountryFromCity(photo.city);
    if (inferred) return normalizeCountry(inferred);
  }
  return null;
}

function formatDate(d) {
  return d.toISOString().split('T')[0];
}

function formatDateTime(d) {
  return d.toISOString();
}

function daysDiff(d1, d2) {
  const diff = Math.abs(d1 - d2);
  return diff / (1000 * 60 * 60 * 24);
}

function generateId() {
  return 'photo-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

function main() {
  console.log('📸 Importing photos as trips/activities...\n');
  console.log(`⚙️  Config: year ${MIN_YEAR}-${MAX_YEAR}, merge window ${MERGE_WINDOW_DAYS} days\n`);
  
  const db = new Database(DB_PATH, { readonly: true });
  
  // Get all photos with location data
  const photos = db.prepare(`
    SELECT id, file_path, filename, date_taken, latitude, longitude, 
           location_name, location_address, country, city, folder_source, sha256
    FROM photos 
    WHERE (country IS NOT NULL AND country != '') 
       OR (city IS NOT NULL AND city != '')
       OR (latitude IS NOT NULL AND longitude IS NOT NULL)
    ORDER BY date_taken ASC, file_path ASC
  `).all();
  
  console.log(`Found ${photos.length} photos with location data`);
  
  // Enrich photos with best date and normalized country
  const enriched = photos.map(p => {
    const date = getBestDate(p);
    const country = getCountry(p);
    return {
      ...p,
      bestDate: date,
      country: country,
      hasGPS: p.latitude !== null && p.longitude !== null
    };
  }).filter(p => {
    if (!p.bestDate || !p.country) return false;
    const year = p.bestDate.getFullYear();
    return year >= MIN_YEAR && year <= MAX_YEAR;
  });
  
  console.log(`After filtering (year ${MIN_YEAR}-${MAX_YEAR}): ${enriched.length} photos with date + country`);
  
  // Group by country + year
  const byCountryYear = new Map();
  for (const p of enriched) {
    const year = p.bestDate.getFullYear();
    const key = `${p.country}-${year}`;
    if (!byCountryYear.has(key)) byCountryYear.set(key, { country: p.country, year, photos: [] });
    byCountryYear.get(key).photos.push(p);
  }
  
  console.log(`\n📍 Country-Year groups: ${byCountryYear.size}`);
  
  // Sort groups by date (earliest photo in group)
  const groups = Array.from(byCountryYear.values()).sort((a, b) => {
    const aFirst = new Date(Math.min(...a.photos.map(p => p.bestDate.getTime())));
    const bFirst = new Date(Math.min(...b.photos.map(p => p.bestDate.getTime())));
    return aFirst - bFirst;
  });
  
  // Merge consecutive countries within window into trips
  const trips = [];
  let currentTrip = null;
  
  for (const group of groups) {
    const groupFirstDate = new Date(Math.min(...group.photos.map(p => p.bestDate.getTime())));
    const groupLastDate = new Date(Math.max(...group.photos.map(p => p.bestDate.getTime())));
    
    if (!currentTrip) {
      currentTrip = {
        id: `trip-${generateId()}`,
        name: `${group.country} ${group.year}`,
        destination: group.country,
        color: 'indigo',
        countries: [group.country],
        startDate: groupFirstDate,
        endDate: groupLastDate,
        groups: [group]
      };
    } else {
      const lastGroup = currentTrip.groups[currentTrip.groups.length - 1];
      const lastDate = new Date(Math.max(...lastGroup.photos.map(p => p.bestDate.getTime())));
      const gap = daysDiff(lastDate, groupFirstDate);
      
      if (gap <= MERGE_WINDOW_DAYS) {
        // Same trip — merge countries
        currentTrip.countries.push(group.country);
        currentTrip.endDate = groupLastDate;
        currentTrip.destination = currentTrip.countries.join(', ');
        currentTrip.name = `${currentTrip.countries[0]} ${currentTrip.groups[0].year} ${currentTrip.countries.length > 1 ? '+' : ''}`;
        currentTrip.groups.push(group);
      } else {
        // New trip — gap too large
        trips.push(currentTrip);
        currentTrip = {
          id: `trip-${generateId()}`,
          name: `${group.country} ${group.year}`,
          destination: group.country,
          color: 'indigo',
          countries: [group.country],
          startDate: groupFirstDate,
          endDate: groupLastDate,
          groups: [group]
        };
      }
    }
  }
  if (currentTrip) trips.push(currentTrip);
  
  console.log(`\n🧳 Created ${trips.length} trips`);
  
  // Generate activities per day per country
  const activities = [];
  
  for (const trip of trips) {
    for (const group of trip.groups) {
      // Group photos by date
      const byDate = new Map();
      for (const p of group.photos) {
        const dateKey = formatDate(p.bestDate);
        if (!byDate.has(dateKey)) byDate.set(dateKey, []);
        byDate.get(dateKey).push(p);
      }
      
      for (const [dateKey, dayPhotos] of byDate) {
        if (dayPhotos.length < MIN_PHOTOS_PER_DAY) continue;
        
        // Pick representative photo (first with GPS, or first)
        const repPhoto = dayPhotos.find(p => p.hasGPS) || dayPhotos[0];
        
        const locationParts = [];
        if (repPhoto.city) locationParts.push(repPhoto.city);
        if (repPhoto.location_name) locationParts.push(repPhoto.location_name);
        if (repPhoto.country) locationParts.push(repPhoto.country);
        const location = locationParts.join(', ') || group.country;
        
        const activity = {
          id: generateId(),
          fileName: `${dayPhotos.length} fotos - ${dateKey}`,
          mimeType: 'application/vnd.photo-group',
          isTravelDocument: true,
          category: 'activity',
          supplier: 'Fotos personales',
          title: `Día en ${group.country}`,
          startDate: dateKey,
          startTime: dayPhotos[0].bestDate.toTimeString().slice(0, 5),
          endDate: dateKey,
          endTime: dayPhotos[dayPhotos.length - 1].bestDate.toTimeString().slice(0, 5),
          confirmationNumber: `PHOTO-${group.country}-${dateKey.replace(/-/g, '')}`,
          location: location,
          passengerOrGuestName: 'Fotos de viaje',
          price: 0,
          currency: 'EUR',
          details: `${dayPhotos.length} fotos tomadas el ${dateKey} en ${group.country}${repPhoto.city ? ` (${repPhoto.city})` : ''}. Primera: ${repPhoto.filename}`,
          summary: `Actividad generada automáticamente desde ${dayPhotos.length} fotos en ${group.country}`,
          iconLink: '',
          tripId: trip.id,
          // Custom fields for photo linkage
          _photoIds: dayPhotos.map(p => p.id),
          _photoPaths: dayPhotos.map(p => p.file_path),
          _representativePhoto: repPhoto.id,
          _country: group.country,
          _lat: repPhoto.latitude,
          _lng: repPhoto.longitude
        };
        activities.push(activity);
      }
    }
  }
  
  console.log(`\n🎯 Generated ${activities.length} activities across ${trips.length} trips`);
  
  // Prepare output
  const output = {
    trips,
    activities,
    generatedAt: new Date().toISOString(),
    config: { MIN_YEAR, MAX_YEAR, MERGE_WINDOW_DAYS },
    stats: {
      totalPhotos: enriched.length,
      trips: trips.length,
      activities: activities.length,
      countries: [...new Set(trips.flatMap(t => t.countries))],
      yearRange: trips.length > 0 ? 
        `${Math.min(...trips.map(t => t.startDate.getFullYear()))}-${Math.max(...trips.map(t => t.endDate.getFullYear()))}` : 'N/A'
    }
  };
  
  // Save JSON for review
  if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const outFile = path.join(OUTPUT_DIR, `photo-trips-${Date.now()}.json`);
  fs.writeFileSync(outFile, JSON.stringify(output, null, 2));
  console.log(`\n💾 Saved to: ${outFile}`);
  
  // Print summary
  console.log('\n📊 TRIP SUMMARY:');
  for (const trip of trips) {
    const tripActivities = activities.filter(a => a.tripId === trip.id);
    console.log(`  ${trip.name} (${formatDate(trip.startDate)} - ${formatDate(trip.endDate)})`);
    console.log(`    Countries: ${trip.countries.join(', ')}`);
    console.log(`    Activities: ${tripActivities.length}`);
    const byCountry = {};
    for (const a of tripActivities) {
      byCountry[a._country] = (byCountry[a._country] || 0) + 1;
    }
    for (const [c, cnt] of Object.entries(byCountry)) {
      console.log(`      ${c}: ${cnt} days`);
    }
  }
  
  // Also generate localStorage-compatible format
  const bookingsForStorage = activities.map(a => ({
    ...a,
    // Ensure compatibility with TravelBooking type
    webViewLink: a._photoPaths[0] ? `file://${a._photoPaths[0].replace(/\\/g, '/')}` : '',
    baseUrl: 'local-photos'
  }));
  
  const storageFile = path.join(OUTPUT_DIR, `travel_bookings_import_${Date.now()}.json`);
  fs.writeFileSync(storageFile, JSON.stringify(bookingsForStorage, null, 2));
  console.log(`\n📦 localStorage import file: ${storageFile}`);
  console.log('\n✅ To import:');
  console.log('   1. Open browser devtools on the app');
  console.log('   2. Run: localStorage.setItem("travel_bookings", `<content of file>`)');
  console.log('   3. Refresh page');
  console.log('\n↩️  To revert: localStorage.removeItem("travel_bookings")');
  
  db.close();
}

main();