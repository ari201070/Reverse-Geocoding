# Evaluación Técnica: Nuevas Herramientas GIS y Geolocalización (Adición)

## 1. Contexto y Principios
- **Regla Estricta:** No borrar ni modificar ningún código existente en los microservicios/APIs.
- **Filosofía:** Evaluar la incorporación de estas librerías/APIs como capas adicionales en la cascada de resolución de ubicaciones y geocodificación inversa.

---

## 2. Análisis de las Herramientas Solicitadas

### A. GeoPy (`geopy`)
* **Repositorio:** [GitHub - geopy/geopy](https://github.com/geopy/geopy)
* **Descripción:** Cliente Python unificado para múltiples servicios de geocodificación (Nominatim/OSM, OpenCage, Photon, Bing, BAN, etc.).
* **Utilidad para el Proyecto:**
  - Proporciona una interfaz limpia y estándar con soporte nativo de **Rate Limiting** (`RateLimiter`) para no saturar APIs FOSS como Nominatim u Overpass.
  - Facilita cálculos de distancia geodésica (`geopy.distance.geodesic`) y azimut/heading para la desambiguación de vectores de cámara.
  - Ideal para scripts de procesamiento en lote (Python batch workers/microservicios).

### B. GeoPyTool
* **Repositorio:** [GitHub - GeoPyTool/GeoPyTool](https://github.com/GeoPyTool/GeoPyTool)
* **Descripción:** Aplicación GUI en Python diseñada para procesamiento geológico y geoquímico.
* **Evaluación:** Enfocada en análisis geológico/mineralógico. No aplica directamente al motor de geocodificación inversa de fotos de viajes.

### C. Geoapify Reverse Geocoding API
* **Sitio Web:** [Geoapify Reverse Geocoding](https://www.geoapify.com/reverse-geocoding-api/)
* **Descripción:** Servicio comercial/freemium de geocodificación basada en OpenStreetMap. Ofrece 3,000 peticiones diarias en su plan gratuito ($0).
* **Utilidad para el Proyecto:**
  - Excelente candidato para añadirse como **Nivel de Fallback FOSS/Freemium** en la cascada de geocodificación junto con OpenCage y Photon.
  - Retorna datos estructurados limpios (POI, calle, ciudad, país, código H3/place_id).

---

## 3. Plan de Integración (Solo Adición Futura)

```
CASCADA DE GEOCODIFICACIÓN INVERSA (AMPLIADA)
├── 1. Caché Espacial Local (PostGIS / SQLite + H3 Res 9) -> 0.1ms (Zero OPEX)
├── 2. Servidores FOSS Locales (Photon / Overpass / Nominatim)
├── 3. GeoPy (Python RateLimiter Wrapper sobre Nominatim/Photon) [NUEVO]
├── 4. Geoapify API (Plan Gratuito 3,000 req/día) [NUEVO FALLBACK]
└── 5. OpenCage API (Plan Gratuito 2,500 req/día)
```

### Acciones recomendadas a futuro (después de instalar dependencies si se autoriza):
1. Añadir `geopy` en los entornos de Python del proyecto (microservicios/Colab/Jupyter).
2. Agregar un handler opcional para Geoapify en `api/find-poi.js` utilizando la clave gratuita sin modificar la lógica existente.
