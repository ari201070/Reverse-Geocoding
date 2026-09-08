/**
 * api/utils/landmark-context.js
 * Utility to identify generic landmark names (plazas, churches, parks, etc.) in Argentina
 * and dynamically contextualize them by appending their corresponding city or province name.
 */

// Ciudades del itinerario de Argentina Aventura Familiar con coordenadas para geofencing de precisión
export const ITINERARY_CITIES = [
    { name: "Buenos Aires", lat: -34.6037, lng: -58.3816 },
    { name: "Rosario", lat: -32.9468, lng: -60.6393 },
    { name: "Bariloche", lat: -41.1335, lng: -71.3103 },
    { name: "Mendoza", lat: -32.8895, lng: -68.8458 },
    { name: "Malargüe", lat: -35.4740, lng: -69.5841 },
    { name: "Jujuy", lat: -24.1858, lng: -65.2995 },
    { name: "Salta", lat: -24.7891, lng: -65.4103 },
    { name: "Iguazú", lat: -25.5991, lng: -54.5736 },
    { name: "Corrientes", lat: -27.4692, lng: -58.8306 },
    { name: "Iberá", lat: -28.5306, lng: -57.1917 }
];

/**
 * Contextualiza nombres de landmarks genéricos (plazas, catedrales, etc.) agregando
 * la ciudad o provincia a la que pertenecen según su dirección o sus coordenadas.
 * 
 * @param {string} name Nombre original del POI
 * @param {string} address Dirección formateada del POI
 * @param {number} lat Latitud de la foto/POI
 * @param {number} lng Longitud de la foto/POI
 * @returns {string} Nombre contextualizado
 */
export function contextualizeLandmarkName(name, address, lat, lng) {
    if (!name) return name;
    
    // Palabras clave que representan landmarks genéricos propensos a duplicarse en muchas ciudades
    const GENERIC_LANDMARKS_REGEX = /(?:plaza|square|catedral|cathedral|centro c\u00edvico|centro civico|cabildo|parque|park|monumento|monument|bas\u00edlica|basilica|iglesia|church|capilla|chapel|mirador|cerro|lago|lake|laguna|aeropuerto|airport|terminal|estaci\u00f3n|estacion|paseo|boulevard|bulevar|museo|museum|anfiteatro|teatro|palacio|parroquia)/i;
    
    if (!GENERIC_LANDMARKS_REGEX.test(name)) {
        return name; // No es un landmark genérico, no necesita contextualizarse
    }

    let detectedCity = null;

    // 1. Si tenemos coordenadas GPS, el Geofencing con las ciudades del itinerario es el método más robusto y preciso (Consistencia de Itinerario)
    if (lat !== null && lng !== null && !isNaN(lat) && !isNaN(lng)) {
        let minDistance = Infinity;
        let closestCity = null;

        for (const city of ITINERARY_CITIES) {
            const dLat = lat - city.lat;
            const dLng = lng - city.lng;
            const dist = Math.sqrt(dLat * dLat + dLng * dLng); // Distancia euclidiana aproximada
            if (dist < minDistance) {
                minDistance = dist;
                closestCity = city;
            }
        }

        // Si está a menos de 1.5 grados (~150 km) de una ciudad del itinerario
        if (closestCity && minDistance < 1.5) {
            detectedCity = closestCity.name;
        }
    }

    // 2. Si no se detectó mediante GPS (por ejemplo coordenadas nulas), analizar la dirección de forma inteligente
    if (!detectedCity && address && typeof address === 'string') {
        const addressClean = address.replace(/[.,]/g, ' ').toLowerCase();
        
        // Buscar coincidencia exacta con ciudades del itinerario en la dirección
        for (const city of ITINERARY_CITIES) {
            const cityLower = city.name.toLowerCase();
            const regex = new RegExp(`\\b${cityLower}\\b`, 'i');
            if (regex.test(addressClean)) {
                detectedCity = city.name;
                break;
            }
        }
        
        // Si no se encontró coincidencia directa con el itinerario, intentar extraer del penúltimo/último elemento
        if (!detectedCity) {
            const parts = address.split(',').map(p => p.trim());
            if (parts.length >= 2) {
                let candidate = parts[parts.length - 2];
                if (candidate.toLowerCase() === 'argentina' && parts.length >= 3) {
                    candidate = parts[parts.length - 3];
                }
                if (candidate) {
                    // Quitar código postal argentino CPA o CP numérico estándar (p. ej. A4400, 4400, etc.)
                    let cleaned = candidate.replace(/\b[A-Z]?\d{4}[A-Z]{0,3}\b/g, '').trim();
                    cleaned = cleaned.replace(/\bargentina\b/gi, '').trim();
                    
                    // Expresión regular para descartar nombres de calles y palabras que no son ciudades
                    const STREET_KEYWORDS = /\b(?:avenida|av|calle|pje|pasaje|ruta|nro|no|altura|mitre|espa\u00f1a|caseros|belgrano|san mart\u00edn|san martin|sarmiento|alberdi|urquiza|boedo|moreno|rivadavia|balcarce|9 de julio|julio)\b/i;
                    
                    if (cleaned && cleaned.length > 2 && cleaned.length < 30 && !STREET_KEYWORDS.test(cleaned)) {
                        detectedCity = cleaned;
                    }
                }
            }
        }
    }

    // 3. Añadir la ciudad al nombre del landmark si no está ya contenida
    if (detectedCity) {
        const nameLower = name.toLowerCase();
        const cityLower = detectedCity.toLowerCase();
        
        if (!nameLower.includes(cityLower)) {
            let alreadyContained = false;
            if (cityLower === 'bariloche' && nameLower.includes('san carlos de bariloche')) alreadyContained = true;
            if (cityLower === 'jujuy' && nameLower.includes('san salvador de jujuy')) alreadyContained = true;
            
            if (!alreadyContained) {
                return `${name}, ${detectedCity}`;
            }
        }
    }

    return name;
}
