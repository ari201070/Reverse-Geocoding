/**
 * KnownTrips - Lista hardcodeada de viajes conocidos basada en documentos de booking
 * 
 * Fuente de verdad: F:\Documentos_Viaje\ y G:\האחסון שלי\
 * Cada viaje tiene fechas exactas extraídas de los documentos de reserva
 */

export const KNOWN_TRIPS = [
  {
    id: 'argentina-2011',
    name: 'Argentina 2011-2012',
    type: 'international',
    country: 'Argentina',
    cities: ['Buenos Aires', 'Calafate', 'Trevelin', 'Los Antiguos', 'Glaciar Perito Moreno', 'Caleta Valdés', 'Puerto Pirámides'],
    startDate: '2011-11-07',
    endDate: '2012-02-06',
    documents: [
      'F:\\Documentos_Viaje\\2011\\Noviembre\\Booking_BuenosAires_2011_HotelMundial.png',
    ],
    notes: 'Viaje por Patagonia. Las fotos con fecha 2026 son de subida/actualización.',
  },
  {
    id: 'slovenia-2015',
    name: 'Eslovenia 2015',
    type: 'international',
    country: 'Slovenia',
    cities: ['Bled', 'Podhom', 'Ribčev Laz', 'Ukanc', 'Bohinjska Bistrica', 'Stara Fužina', 'Bohinjska Bela'],
    startDate: '2015-07-02',
    endDate: '2015-07-06',
    documents: [
      'F:\\Documentos_Viaje\\2015\\Julio\\Booking_Slovenia_2015_ApartmentsZorc.png',
      'F:\\Documentos_Viaje\\2015\\Julio\\Booking_Slovenia_2015_GarniHotelAzur.png',
      'F:\\Documentos_Viaje\\2015\\Julio\\Booking_Slovenia_2015_HotelKrim.png',
      'F:\\Documentos_Viaje\\2015\\Julio\\Booking_Slovenia_2015_HotelSavica.png',
    ],
    notes: '4 reservas de hotel confirmadas.',
  },
  {
    id: 'croatia-montenegro-2010',
    name: 'Croacia+Montenegro 2010',
    type: 'international',
    country: 'Croatia',
    countries: ['Croatia', 'Montenegro'],
    cities: ['Dubrovnik', 'Podgorica', 'Kolašin', 'Budva', 'Velji Bostur', 'Kotor', 'Škaljari'],
    startDate: '2010-06-24',
    endDate: '2010-06-30',
    documents: [],
    notes: 'Viaje por Croacia y Montenegro.',
  },
  {
    id: 'crete-2013',
    name: 'Creta 2013',
    type: 'international',
    country: 'Crete',
    cities: ['Chersonissos', 'Heraklion', 'Psychro'],
    startDate: '2013-07-23',
    endDate: '2013-07-27',
    documents: [],
    notes: 'Todas las fotos están en Creta, no en Grecia continental.',
  },
  {
    id: 'italy-2023',
    name: 'Italia 2023',
    type: 'international',
    country: 'Italy',
    cities: ['Florence', 'Pisa'],
    startDate: '2023-10-03',
    endDate: '2023-10-11',
    documents: [
      'G:\\האחסון שלי\\גברים רעבים באיטליה\\Booking_Italia_2023_Hoteles.png',
      'G:\\האחסון שלי\\גברים רעבים באיטליה\\Hotel Soperga_ אישור.pdf',
    ],
    notes: 'Viaje de hombres. Solo Firenze y Pisa.',
  },
  {
    id: 'bosnia-2023',
    name: 'Bosnia 2023',
    type: 'international',
    country: 'Bosnia and Herzegovina',
    cities: ['Sarajevo', 'Jajce'],
    startDate: '2023-05-01',
    endDate: '2023-05-05',
    documents: [
      'F:\\Documentos_Viaje\\2023\\Mayo\\סיכום טיול בוסניה 2023 עבור אריאל פליאר.docx',
    ],
    notes: 'Solo 1 foto geolocalizada, pero documentos confirman el viaje.',
  },
  {
    id: 'argentina-2025',
    name: 'Argentina 2025',
    type: 'international',
    country: 'Argentina',
    cities: ['Buenos Aires', 'Tigre', 'Rosario', 'Villa Traful', 'Bariloche', 'El Bolsón', 'Mendoza', 'Puente del Inca', 'Salta', 'Iguazú', 'Esteros del Iberá', 'Corrientes'],
    startDate: '2025-09-26',
    endDate: '2025-10-30',
    documents: [
      'F:\\Documentos_Viaje\\2025\\Septiembre\\Booking_Argentina_2025_Traslado.png',
      'F:\\Documentos_Viaje\\2025\\Octubre\\Booking_Argentina_2025_Hoteles.png',
      'F:\\Documentos_Viaje\\2025\\Octubre\\itinerary_Y0HBMB59-1.pdf',
      'F:\\Documentos_Viaje\\2025\\Octubre\\Confirmación_Fuente Mayor Hotel Centro.pdf',
    ],
    notes: 'Viaje familiar de 30 días. Itinerario completo documentado.',
  },
  {
    id: 'denmark-2024',
    name: 'Dinamarca 2024',
    type: 'international',
    country: 'Denmark',
    cities: ['Copenhagen', 'Hillerod'],
    startDate: '2024-09-15',
    endDate: '2024-09-20',
    documents: [
      'G:\\האחסון שלי\\vouchersBest Western Hotel Hillerod-Hillerod-16-Sep-FLIER.pdf',
      'G:\\האחסון שלי\\vouchersHotel Astoria Bw Signature Collection-Copenhagen-15-Sep-flier.pdf',
      'G:\\האחסון שלי\\vouchersHotel Astoria Bw Signature Collection-Copenhagen-20-Sep-flier.pdf',
    ],
    notes: 'Viaje a Dinamarca. Fotos sin geolocalización.',
  },
];

/**
 * Obtiene un viaje por su ID
 */
export function getTripById(tripId) {
  return KNOWN_TRIPS.find(trip => trip.id === tripId);
}

/**
 * Obtiene todos los viajes de un país
 */
export function getTripsByCountry(country) {
  return KNOWN_TRIPS.filter(trip => 
    trip.country === country || 
    (trip.countries && trip.countries.includes(country))
  );
}

/**
 * Obtiene el viaje que contiene una fecha específica
 */
export function getTripByDate(date, country) {
  const dateStr = date instanceof Date ? date.toISOString().split('T')[0] : date;
  
  return KNOWN_TRIPS.find(trip => {
    // Verificar país
    if (country && trip.country !== country && 
        (!trip.countries || !trip.countries.includes(country))) {
      return false;
    }
    
    // Verificar rango de fechas
    if (trip.startDate && trip.endDate) {
      return dateStr >= trip.startDate && dateStr <= trip.endDate;
    }
    
    return false;
  });
}

export default KNOWN_TRIPS;