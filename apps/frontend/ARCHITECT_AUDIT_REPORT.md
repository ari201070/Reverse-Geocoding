# Auditoría Completa de Herramientas - Informe para Arquitecto

**Fecha:** 2026-07-23
**Objetivo:** Reorganizar 34,992 fotos en estructura País/Ciudad/Viaje usando todas las herramientas disponibles

---

## 1. ESTADO ACTUAL DEL PROBLEMA

### Estructura actual (INCORRECTA):
```
F:\2023\Octubre\גברים רעבים באיטליה-2023\xiomi\  ← 20 fotos mezcladas
F:\2011\Noviembre\טיול לארגנטינה\  ← 880 fotos mezcladas
F:\2010\Junio\  ← 245 fotos mezcladas
```

### Estructura deseada:
```
F:\2023\Octubre\Italia 2023\Pisa\xiomi\
F:\2011\Noviembre\Argentina 2011-2012\Bariloche\
F:\2010\Junio\Croacia+Montenegro 2010\Dubrovnik\
```

---

## 2. INVENTARIO COMPLETO DE HERRANDAS DISPONIBLES

### 2.1 APIs Externas (`api/`)

| Herramienta | Capacidad | Estado de Uso | Prioridad |
|------------|-----------|---------------|-----------|
| **analyze-image.js** | Vision cascade: Ollama/Moondream → OpenRouter → Gemini. Detecta landmarks, OCR, labels | ❌ NO USADA para reorganización | CRÍTICO |
| **resolve-puzzle.js** | Orquestador agentic batch con 5 tools: rankAnchors, cleanupOCR, fuzzyReconcileOCR, analyzeFisonomia, analyzeSolarSync, resolvePoi | ❌ NO USADA para reorganización | CRÍTICO |
| **find-poi.js** | 5 niveles: H3 Cache → Local DB → Photon → Overpass → OpenCage → Country boundary | ✅ Usada para enrichment GPS (6,754 fotos) | MEDIO |
| **spatial-utils.js** | H3 R9 indexing, Ray-Casting, GeoJSON world countries, sovereign reverse geocoding | ✅ Usada internamente | ALTO |
| **generate-qa-map.js** | Generador de mapas QA con indexación recursiva de disco | ❌ NO USADA | MEDIO |
| **geojson-cache.js** | Endpoint unificado de FeatureCollections (country boundaries + known_places) | ❌ NO USADA | MEDIO |
| **analyze-exif.js** | Parser EXIF puro JS con fallback Python | ❌ NO USADA | ALTO |

### 2.2 Servicios Modulares (`mcp-photo-catalog/src/services/`)

| Servicio | Capacidad | Estado de Uso |
|----------|-----------|---------------|
| **KnownTrips.js** | 8 viajes hardcodeados con fechas exactas de booking docs | ✅ Fuente de verdad |
| **TripAggregator.js** | Agrupación documento-primero: docs → H3 → asignación → micro-actividades → consenso | ✅ Usado pero incompleto |
| **TripExporter.js** | Exportación JSON para localStorage | ✅ Usado |
| **CountryNormalizer.js** | Normalización de países (Greece→Crete, Hebrew/Spanish mappings) | ✅ Usado |
| **H3Service.js** | Índices H3 R9 | ✅ Usado |
| **SpatialCacheClient.js** | Cache en memoria H3 | ✅ Usado |
| **ConsensusEngine.js** | Scoring Antigravity 2.0 | ✅ Usado |
| **PhotoRepository.js** | Capa SQLite de lectura | ✅ Usado |
| **BookingDocumentParser.js** | Escáner de documentos de booking | ✅ Usado |

### 2.3 Scripts Existentes (`mcp-photo-catalog/`)

| Script | Capacidad | Estado |
|--------|-----------|--------|
| **propagate_metadata.mjs** | Propagación masiva de metadata (país, ciudad, trip) | ✅ Completado (100% país) |
| **classify_no_country.mjs** | Clasificación por keywords, KnownTrips, sibling folders | ✅ Completado |
| **enrich_overpass_clusters.mjs** | Enriquecimiento GPS con Overpass API | ✅ Completado (100% GPS) |
| **move_duplicates_to_papelera.mjs** | Movimiento de duplicados verificados | ✅ Completado |

---

## 3. CAPACIDADES NO APROVECHADAS (CRÍTICO)

### 3.1 Vision API para Clasificación Automática
**analyze-image.js** puede:
- Detectar **landmarks** automáticamente (Torre de Pisa, Glaciar Perito Moreno, etc.)
- Extraer **texto/OCR** de carteles, calles, señales
- Clasificar **entornos** (playa, montaña, ciudad, desierto)
- **Potencial:** Clasificar fotos sin GPS/fecha usando visión artificial

### 3.2 Orquestador Agentic para Batch Processing
**resolve-puzzle.js** puede:
- Procesar **miles de fotos en batch** con consenso
- Usar **múltiples tools** en paralelo (vision + geocoding + OCR)
- Aplicar **fuzzy matching** para reconciliar nombres
- **Potencial:** Procesar las 18,536 fotos de WhatsApp/Israel que no tienen trip asignado

### 3.3 Detección de Patrones Temporales
**TripAggregator.js** puede:
- Detectar **micro-actividades** (fotos agrupadas por H3 + fecha)
- Fusionar actividades en **viajes** usando ventanas temporales
- Crear **actividades locales** para fotos no asignadas
- **Potencial:** Detectar viajes no documentados (fotos familiares, excursiones locales)

### 3.4 Enriquecimiento de Ciudad/POI
**find-poi.js** puede:
- Resolver coordenadas a **nombres de lugares específicos**
- Usar **múltiples fuentes** con cascada de fallback
- **Potencial:** Asignar ciudades a las 6,754 fotos GPS que solo tienen location_name

---

## 4. FOTO EJEMPLO - ANÁLISIS COMPLETO

### Foto: `(Lago Puelo)בדרך ללאגו פואלו x.jpg`
- **Ubicación actual:** `F:\2011\Noviembre\טיול לארגנטינה\`
- **GPS:** lat: -42.0715, lng: -71.5714
- **País detectado:** Argentina ✅
- **Ciudad actual:** (vacía) ❌
- **Viaje asignado:** (ninguno) ❌

### Solución con herramientas disponibles:
1. **find-poi.js** → Resolver GPS a "Lago Puelo, Chubut, Argentina"
2. **KnownTrips.js** → Detectar "Argentina 2011-2012" (fecha: 2011-11-07 a 2012-02-06)
3. **TripAggregator.js** → Asignar a trip "argentina-2011"
4. **Mover a:** `F:\2011\Noviembre\Argentina 2011-2012\Lago Puelo\(Lago Puelo)בדרך ללאגו פואלו x.jpg`

---

## 5. PLAN PROPUESTO - FASES

### Fase 1: Enriquecimiento Masivo (1-2 horas)
1. Ejecutar **find-poi.js** en batch para todas las fotos GPS sin ciudad
2. Ejecutar **analyze-image.js** para fotos sin GPS (muestra representativa)
3. Actualizar DB con ciudades/POIs detectados

### Fase 2: Asignación de Trips (30 min)
1. Ejecutar **TripAggregator.process()** con KnownTrips
2. Asignar fotos a viajes existentes
3. Detectar micro-actividades para fotos no asignadas

### Fase 3: Plan de Reorganización (script)
1. Generar script de movimiento basado en:
   - País (de DB)
   - Ciudad (de find-poi)
   - Viaje (de TripAggregator)
2. Estructura destino: `F:\{Year}\{TripName}\{City}\{filename}`
3. Validación antes de ejecutar

### Fase 4: Ejecución (manual)
1. Ejecutar script de reorganización
2. Verificar integridad
3. Actualizar DB con nuevas rutas

---

## 6. RECOMENDACIONES DEL ARQUITECTO

Por favor, revisa este informe y confirma:
1. ¿Es correcta la estrategia de usar vision API para fotos sin GPS?
2. ¿Deberíamos procesar todas las fotos o solo una muestra?
3. ¿Cuál es el orden óptimo de fases?
4. ¿Hay riesgos que no estamos considerando?

---

**Architect, por favor analiza este informe y proporciona tu recomendación.**
