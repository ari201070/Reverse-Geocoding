// api/utils/consensus-engine.js
// Motor de Consenso Soberano para resolver la "Verdad del Lugar" combinando
// coordenadas, datos de visión (OCR/Hitos), límites GeoJSON y clics manuales.

import * as h3 from 'h3-js';

/**
 * Consolida múltiples candidatos e indicios espaciales/visuales para deducir la ubicación final.
 * 
 * @param {Object} params
 * @param {Object} params.coords Coordenadas del punto [lat, lng]
 * @param {Object} params.visionData Datos devueltos por analyze-image ({ labels, landmarks, texts, status })
 * @param {Object} params.geocodingData Datos del geolocalizador inverso ({ name, address, source, confidence })
 * @param {boolean} params.isManual true si el usuario posicionó manualmente la foto en el mapa
 * 
 * @returns {Object} Un objeto con la ubicación del consenso, confianza unificada y el razonamiento.
 */
export function resolveLocationConsensus({ coords, visionData, geocodingData, isManual = false }) {
    const { lat, lng } = coords || {};
    const parsedLat = parseFloat(lat);
    const parsedLng = parseFloat(lng);
    
    if (isNaN(parsedLat) || isNaN(parsedLng)) {
        return {
            success: false,
            error: "Coordenadas no válidas para calcular consenso"
        };
    }

    const h3Index = h3.latLngToCell(parsedLat, parsedLng, 9);
    
    // Si la posición fue colocada manualmente por el usuario, tiene prioridad absoluta (100% verídica por acción humana)
    if (isManual) {
        const placeName = geocodingData?.name || `Ubicación manual (${parsedLat.toFixed(4)}, ${parsedLng.toFixed(4)})`;
        return {
            success: true,
            data: {
                name: placeName,
                address: geocodingData?.address || "Establecido por el usuario en el mapa",
                coords: { lat: parsedLat, lng: parsedLng },
                source: "CONSENSO_MANUAL_USUARIO",
                confidence: 1.0,
                h3Index: h3Index
            },
            reasoning: "El usuario ha ubicado manualmente la fotografía en el mapa interactivo de Leaflet, anulando cualquier discrepancia de metadatos o fallos de API."
        };
    }

    // Inicializar candidatos de consenso
    const candidates = [];

    // 1. Agregar el resultado de geocodificación inversa (Local GeoJSON, OpenCage o Google)
    if (geocodingData && geocodingData.name) {
        let weight = geocodingData.confidence || 0.5;
        // Ajustar pesos de origen
        if (geocodingData.source === 'GOOGLE_PLACES_NEW' || geocodingData.source === 'GOOGLE_PLACES_TEXT_SEARCH') {
            weight = 0.99;
        } else if (geocodingData.source === 'LOCAL_COUNTRY_BOUNDARIES_H3') {
            weight = 0.85;
        } else if (geocodingData.source === 'OPENCAGE') {
            weight = 0.80;
        } else if (geocodingData.source === 'LOCAL_SPATIAL_RADIUS_DB') {
            weight = 0.95;
        }

        candidates.push({
            name: geocodingData.name,
            address: geocodingData.address || "",
            source: geocodingData.source,
            confidence: weight,
            type: 'GEOGRAPHIC'
        });
    }

    // 2. Extraer indicios de Visión (Landmarks y OCR)
    const visionLandmarks = visionData?.landmarks || [];
    const visionTexts = visionData?.texts || [];

    // Buscar si hay monumentos reconocidos por la Visión Inteligente
    if (visionLandmarks.length > 0) {
        // Un landmark específico detectado por Visión es un candidato extremadamente fuerte
        const bestLandmark = visionLandmarks[0];
        candidates.push({
            name: bestLandmark,
            address: visionTexts.slice(0, 3).join(', ') || "Hito visual detectado",
            source: visionData.status || "VISION_AI",
            confidence: 0.92, // Alta confianza para reconocimiento de hitos locales
            type: 'VISUAL_LANDMARK'
        });
    }

    // Si no hay candidatos, devolver fallback básico
    if (candidates.length === 0) {
        return {
            success: true,
            data: {
                name: `${parsedLat.toFixed(4)}, ${parsedLng.toFixed(4)}`,
                address: "Coordenadas del sensor GPS",
                coords: { lat: parsedLat, lng: parsedLng },
                source: "SENSOR_GPS_DIRECTO",
                confidence: 0.5,
                h3Index: h3Index
            },
            reasoning: "Sin pistas de texto, hitos visuales ni coincidencia en el mapa GeoJSON local. Se asumen coordenadas puras del dispositivo."
        };
    }

    // Evaluar coherencia de intersección (Consensus Match)
    // Por ejemplo: si Visión detectó "Catedral" y Geocodificación inversa dice "Bariloche", se combinan
    let consensusName = "";
    let consensusAddress = "";
    let consensusSource = "CONSENSO_ORQUESTADO";
    let consensusConfidence = 0.5;
    let reasoning = "";

    const bestGeo = candidates.find(c => c.type === 'GEOGRAPHIC');
    const bestVisual = candidates.find(c => c.type === 'VISUAL_LANDMARK');

    if (bestGeo && bestVisual) {
        // Fusión perfecta: Hito detectado + País/Localidad geocodificado
        consensusName = `${bestVisual.name}`;
        consensusAddress = bestGeo.address || bestGeo.name;
        consensusConfidence = Math.max(bestGeo.confidence, bestVisual.confidence) + 0.05; // Bono de concordancia múltiple
        if (consensusConfidence > 0.99) consensusConfidence = 0.99;
        consensusSource = "CONSENSO_HITO_Y_GEOGRAFIA";
        reasoning = `Consenso exitoso: Visión Inteligente detectó el monumento '${bestVisual.name}' y la caché local espacial confirmó la geografía en '${bestGeo.name}'.`;
    } else if (bestVisual) {
        consensusName = bestVisual.name;
        consensusAddress = bestVisual.address || "Hito de Visión Local";
        consensusConfidence = bestVisual.confidence;
        consensusSource = bestVisual.source;
        reasoning = `Resolución por Hito Visual: Visión de Ollama/Gemini identificó con precisión '${bestVisual.name}' en la imagen.`;
    } else {
        // Solo tenemos geográfico
        consensusName = bestGeo.name;
        consensusAddress = bestGeo.address || "Ubicación geográfica resuelta";
        consensusConfidence = bestGeo.confidence;
        consensusSource = bestGeo.source;
        reasoning = `Resolución por Mapa: Coordenadas resueltas localmente contra base de datos o fronteras GeoJSON de países.`;
    }

    // Si el OCR de visión (texts) contiene palabras que reafirman el nombre del lugar, incrementamos la confianza
    if (visionTexts.length > 0 && consensusName) {
        const lowerName = consensusName.toLowerCase();
        const matchesOcr = visionTexts.some(txt => {
            const words = txt.toLowerCase().split(/\s+/).filter(w => w.length > 3);
            return words.some(w => lowerName.includes(w));
        });
        if (matchesOcr) {
            consensusConfidence += 0.03;
            if (consensusConfidence > 0.99) consensusConfidence = 0.99;
            reasoning += " El OCR de la foto reafirma la veracidad de la ubicación mediante coincidencia textual.";
        }
    }

    return {
        success: true,
        data: {
            name: consensusName,
            address: consensusAddress,
            coords: { lat: parsedLat, lng: parsedLng },
            source: consensusSource,
            confidence: parseFloat(consensusConfidence.toFixed(2)),
            h3Index: h3Index
        },
        reasoning: reasoning
    };
}
