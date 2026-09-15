// api/utils/spatial-utils.js
// Utilidades espaciales soberanas para reverse geocoding y caché local sin bases de datos externas.
import fs from 'fs';
import path from 'path';
import * as h3 from 'h3-js';

let cachedWorldGeoJson = null;

/**
 * Normaliza las propiedades de un feature de Natural Earth para ser case-insensitive.
 */
export function getCountryProperties(properties) {
    if (!properties) return {};
    return {
        name: properties.NAME || properties.name || properties.ADMIN || properties.admin || "Unknown Country",
        iso_a2: properties.ISO_A2 || properties.iso_a2 || properties.ISO_A2_EH || properties.iso_a2_eh || "XX",
        continent: properties.CONTINENT || properties.continent || "Unknown Continent"
    };
}

/**
 * Obtiene todos los anillos (rings) de un Polygon o MultiPolygon de GeoJSON.
 */
function getRings(geometry) {
    if (!geometry) return [];
    if (geometry.type === 'Polygon') {
        return geometry.coordinates;
    } else if (geometry.type === 'MultiPolygon') {
        const rings = [];
        for (const polygon of geometry.coordinates) {
            for (const ring of polygon) {
                rings.push(ring);
            }
        }
        return rings;
    }
    return [];
}

/**
 * Calcula la caja delimitadora (BBOX) para una geometría.
 * @returns [minLng, minLat, maxLng, maxLat]
 */
export function calculateBBox(geometry) {
    let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
    const rings = getRings(geometry);
    for (const ring of rings) {
        for (const pt of ring) {
            const lng = pt[0];
            const lat = pt[1];
            if (lng < minLng) minLng = lng;
            if (lat < minLat) minLat = lat;
            if (lng > maxLng) maxLng = lng;
            if (lat > maxLat) maxLat = lat;
        }
    }
    return [minLng, minLat, maxLng, maxLat];
}

/**
 * Determina si una coordenada se encuentra dentro de un anillo de polígono.
 * Algoritmo clásico de Ray-Casting (Jordan Curve Theorem).
 */
function isPointInRing(point, ring) {
    const x = point[0]; // lng
    const y = point[1]; // lat
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const xi = ring[i][0], yi = ring[i][1];
        const xj = ring[j][0], yj = ring[j][1];
        
        const intersect = ((yi > y) !== (yj > y))
            && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
    }
    return inside;
}

/**
 * Determina si una coordenada se encuentra dentro de un polígono (tomando en cuenta agujeros).
 */
export function isPointInPolygon(point, polygonCoordinates) {
    // El primer anillo es el contorno exterior
    if (!isPointInRing(point, polygonCoordinates[0])) {
        return false;
    }
    // Los siguientes anillos son agujeros
    for (let i = 1; i < polygonCoordinates.length; i++) {
        if (isPointInRing(point, polygonCoordinates[i])) {
            return false; // Está dentro de un agujero, por lo tanto fuera del polígono
        }
    }
    return true;
}

/**
 * Determina si una coordenada se encuentra dentro de un feature GeoJSON (Polygon o MultiPolygon).
 */
export function isPointInFeature(point, feature) {
    const geom = feature.geometry;
    if (!geom) return false;
    
    // Primero un chequeo BBOX ultra-rápido antes del Ray-Casting
    if (!feature.bbox) {
        feature.bbox = calculateBBox(geom);
    }
    const [minLng, minLat, maxLng, maxLat] = feature.bbox;
    const [lng, lat] = point;
    if (lng < minLng || lng > maxLng || lat < minLat || lat > maxLat) {
        return false; // Fuera del BBOX, omitir ray-casting
    }

    // Ray-casting preciso
    if (geom.type === 'Polygon') {
        return isPointInPolygon(point, geom.coordinates);
    } else if (geom.type === 'MultiPolygon') {
        for (const polygonCoords of geom.coordinates) {
            if (isPointInPolygon(point, polygonCoords)) {
                return true;
            }
        }
    }
    return false;
}

/**
 * Carga de forma perezosa (lazy) el GeoJSON mundial simplificado y lo almacena en RAM.
 */
export function loadWorldGeoJson() {
    if (cachedWorldGeoJson) return cachedWorldGeoJson;
    
    const geoJsonPath = path.join(process.cwd(), '.data', 'world_countries.geojson');
    if (!fs.existsSync(geoJsonPath)) {
        console.warn(`[Spatial Utils] Archivo de países no encontrado en: ${geoJsonPath}`);
        return null;
    }
    
    try {
        console.log(`[Spatial Utils] Cargando y parseando mapa mundial GeoJSON...`);
        const start = Date.now();
        const data = fs.readFileSync(geoJsonPath, 'utf8');
        cachedWorldGeoJson = JSON.parse(data);
        
        // Pre-calcular BBOX para todos los features para acelerar consultas futuras
        if (cachedWorldGeoJson.features) {
            for (const feature of cachedWorldGeoJson.features) {
                feature.bbox = calculateBBox(feature.geometry);
            }
        }
        
        console.log(`[Spatial Utils] Cargado con éxito en ${Date.now() - start}ms. ${cachedWorldGeoJson.features?.length || 0} países cacheteados en RAM.`);
        return cachedWorldGeoJson;
    } catch (err) {
        console.error(`[Spatial Utils] Error al parsear mapa mundial GeoJSON:`, err.message);
        return null;
    }
}

/**
 * Resuelve las coordenadas [lat, lng] localmente en un país.
 * @returns Objeto del país { name, iso_a2, continent } o null
 */
export function findCountryForCoordinate(lat, lng) {
    const geojson = loadWorldGeoJson();
    if (!geojson || !geojson.features) return null;
    
    const point = [parseFloat(lng), parseFloat(lat)];
    for (const feature of geojson.features) {
        if (isPointInFeature(point, feature)) {
            return getCountryProperties(feature.properties);
        }
    }
    return null;
}

let h3Cache = null;
const h3CachePath = path.join(process.cwd(), '.data', 'spatial_h3_cache.json');

function loadH3Cache() {
    if (h3Cache) return h3Cache;
    if (!fs.existsSync(h3CachePath)) {
        h3Cache = {};
        return h3Cache;
    }
    try {
        const data = fs.readFileSync(h3CachePath, 'utf8');
        h3Cache = JSON.parse(data);
        return h3Cache;
    } catch (err) {
        console.error(`[Spatial Utils] Error al cargar caché H3:`, err.message);
        h3Cache = {};
        return h3Cache;
    }
}

function saveH3Cache() {
    if (!h3Cache) return;
    try {
        const dir = path.dirname(h3CachePath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(h3CachePath, JSON.stringify(h3Cache, null, 2), 'utf8');
    } catch (err) {
        console.error(`[Spatial Utils] Error al guardar caché H3:`, err.message);
    }
}

/**
 * Resuelve las coordenadas [lat, lng] localmente usando indexación H3 (Resolución 9) y caché.
 * Si no está cacheado, realiza el ray-casting Point-In-Polygon y lo registra en caché.
 */
export function findCountryForCoordinateWithH3(lat, lng) {
    const latVal = parseFloat(lat);
    const lngVal = parseFloat(lng);
    if (isNaN(latVal) || isNaN(lngVal)) return null;

    // Obtener H3 index a Resolución 9
    let cellIndex;
    try {
        cellIndex = h3.latLngToCell(latVal, lngVal, 9);
    } catch (err) {
        console.warn(`[Spatial Utils] Error calculando celda H3 para [${latVal}, ${lngVal}]:`, err.message);
        return findCountryForCoordinate(latVal, lngVal);
    }

    const cache = loadH3Cache();
    if (cache[cellIndex]) {
        // Encontrado en caché!
        return { ...cache[cellIndex], h3Index: cellIndex, cached: true };
    }

    // No está en caché, calcular usando Point-In-Polygon clásico
    const country = findCountryForCoordinate(latVal, lngVal);
    if (country) {
        cache[cellIndex] = country;
        saveH3Cache();
        return { ...country, h3Index: cellIndex, cached: false };
    }

    // Si no coincide con ningún país (océano/fuera de límites), guardar para evitar repetir PIP
    const oceanValue = { name: "Ocean or Unknown", iso_a2: "XX", continent: "Ocean" };
    cache[cellIndex] = oceanValue;
    saveH3Cache();
    return { ...oceanValue, h3Index: cellIndex, cached: false };
}
