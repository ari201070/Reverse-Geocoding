# Master Prompts para Reverse-Geocoding V2.0 — Fuentes de la Industria + Academia

> **FUENTE DE VERDAD**: NotebookLM (`reverse-geocoding-docs`) — 49 fuentes consultadas
> Incluye: Pricing 2026, Case Studies, Papers Académicos, Provider Comparisons, HIPAA Compliance

---

## 1. PROMPT: Extracción de Coordenadas GPS (Cascading EXIF)

```markdown
# CADENA DE EXTRACCIÓN GPS (Cascading Priority)

## Prioridad de Señales (Top-Down)
1. **EXIF Nativo** → latitude, longitude
2. **XMP (Adobe/Google Photos)** → GPSLatitude, GPSLongitude
3. **IPTC Core** → Metadatos de ubicación
4. **Fallback Visual** → Picarta AI o input manual

## Implementación
```javascript
const coords = await exifr.gps(imageBuffer, {
  gps: true, exif: true, xmp: true,
  pick: ['GPSLatitude', 'GPSLongitude', 'DateTimeOriginal']
});
const normalized = {
  lat: Math.round(coords.latitude * 10000) / 10000,
  lng: Math.round(coords.longitude * 10000) / 10000
};
```
```

---

## 2. PROMPT: Búsqueda de POIs — Cascade 3-Niveles (Actualizado 2026)

```markdown
# ORQUESTADOR DE BÚSQUEDA POI (3-Level Cascade)

## Comparativa de Proveedores 2026

| Proveedor | Free Tier | Costo/k req | Almacenamiento |
|-----------|-----------|-------------|----------------|
| **Google Maps** | 10k/mes | $5.00 | ❌ Prohibido (30 días máx) |
| **HERE** | 1k/día | ~$0.75-0.83 | ✅ Permitido |
| **Mapbox** | 100k/mes | $5.00 | ⚠️ Solo API Permanente |
| **OpenCage** | 2.5k/día | ~$0.50 | ✅ Permitido (sin restricciones) |
| **Geoapify** | 3k/día | $59/mes (100k) | ✅ Permitido |
| **Nominatim** | ∞ (self-hosted) | $0 | ✅ Total |

## Arquitectura Recomendada (Costo-Soberanía)

### Nivel 1: Caché H3 (GRATIS)
```javascript
const h3Index = h3.latLngToCell(lat, lng, 9);
const cached = await memoryStore.findMatch(h3Index);
if (cached) return cached; // ~0ms, $0
```

### Nivel 2: OpenCage (ECONÓMICO + SOBERANÍA)
```javascript
// Header no_record para HIPAA/salud
const response = await fetch(
  `https://api.opencagedata.com/geocode/v1/json?q=${lat},${lng}&key=${OPENCAGE_KEY}&language=es&no_record=true`
);
```

### Nivel 3: Google Places API (ALTA PRECISIÓN)
```javascript
const response = await fetch('https://places.googleapis.com/v1/places:searchNearby', {
  headers: {
    'X-Goog-Api-Key': process.env.GOOGLE_MAPS_API_KEY,
    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.types'
  },
  body: JSON.stringify({
    locationRestriction: {
      circle: { center: { latitude: lat, longitude: lng }, radius: 500 }
    },
    maxResultCount: 1
  })
});
```

## Estrategias de Reducción de Costos
1. **FieldMask estricto**: Solo campos necesarios
2. **Cache H3**: Elimina llamadas redundantes
3. **Redondeo a 4 decimales**: Fuerza colisión en caché (~11m)
4. **Batch Processing**: Agrupar peticiones cuando sea posible
```

---

## 3. PROMPT: Procesamiento en Lote (Puzzle Mode)

```markdown
# LÓGICA DE CONSENSO PARA LOTES

## Identificación de Anchor Photos

| Señal | Score | Acción |
|-------|-------|--------|
| **Landmark Detectado** | 1.0 | Ancla maestra |
| **OCR Corto** (<60 chars) | 0.8 | Búsqueda directa |
| **OCR Largo** (≥60 chars) | 0.4 | Requiere Ollama (phi3) |
| **Solo GPS** | 0.2 | Fallback geocoding |

## Regla de Herencia (15 min)
```javascript
const INHERIT_WINDOW_MS = 15 * 60 * 1000;
const timeDiff = Math.abs(photo.timestamp - masterTimestamp);
const canInherit = timeDiff <= INHERIT_WINDOW_MS;
```

## Algoritmo de Consenso
```javascript
const CONSENSUS_THRESHOLD = 0.75;
const anchorScore = masterAnchor?.score || 0.1;
const consistencyBonus = results.filter(r => r.name === results[0]?.name).length / results.length;
const finalConfidence = Math.min(0.99, (anchorScore * 0.7) + (consistencyBonus * 0.3));
```
```

---

## 4. PROMPT: Best Practices de Caching (Case Study Rover)

```markdown
# CACHING ESCALABLE — De Case Study Rover

## Insights Críticos

### NO usar coordenadas exactas como clave
La precisión de 4 decimales (~10m) genera volumen excesivo de cache misses.

### Usar Geohashes o H3 Index
Agrupar áreas geográficas en una sola clave:

| Resolución | Precisión | Hit Ratio | Caso de Uso |
|------------|-----------|-----------|-------------|
| H3 Res 6 | ~1.2km | 80% | Rural disperso |
| **H3 Res 7** | **~150m** | **78%** | **Óptimo urbano** |
| H3 Res 8 | ~43m | 72% | Alta precisión |
| H3 Res 9 | ~11m | 65% | Ground truth |

**Recomendación**: H3 Res 9 para tu sistema (~11m) con redondeo a 4 decimales.

## Filtrado de Datos Inválidos (Anti-Contaminación)
```javascript
function isValidCoordinate(lat, lng) {
  return (
    lat >= -90 && lat <= 90 &&
    lng >= -180 && lng <= 180 &&
    !(lat === 0 && lng === 0) &&
    !(isNaN(lat) || isNaN(lng))
  );
}
```

## Simulación Pre-Implementación
Antes de implementar, simular con logs de 7 días para predecir hit ratio.

## Lógica de Fallback y Repoblación
```javascript
async function safeGeocode(lat, lng) {
  try {
    const cached = await memoryStore.findMatch(h3Index);
    if (cached) return cached;
  } catch (e) {
    console.warn('[Cache] Failure, querying DB...');
  }
  
  // Fallback a API
  const result = await expensiveGeocodeAPI(lat, lng);
  
  // Repoblar caché inmediatamente
  await memoryStore.savePlace(result);
  return result;
}
```

## Benchmark H3 vs Trigonométricos
| Método | 100 lugares | 10,000 lugares | 1M lugares |
|--------|-------------|----------------|-----------|
| Trigonométrico | 0.3ms | 15ms | 1500ms |
| **H3 B-Tree** | **0.1ms** | **0.1ms** | **0.1ms** |
| **Speedup** | **3x** | **150x** | **15,000x** |
```

---

## 5. PROMPT: Integración Vision API + OCR

```markdown
# DETECCIÓN VISUAL PARA GEOCODING

## Pipeline de Visión

```javascript
const visionResponse = await fetch(
  `https://vision.googleapis.com/v1/images:annotate?key=${GOOGLE_KEY}`,
  {
    method: 'POST',
    body: JSON.stringify({
      requests: [{
        image: { content: base64Image },
        features: [
          { type: 'LABEL_DETECTION', maxResults: 10 },
          { type: 'LANDMARK_DETECTION', maxResults: 3 },
          { type: 'TEXT_DETECTION' }
        ]
      }]
    })
  }
);
```

## Mapeo Contextual

| Label Detectado | Tipo de Búsqueda Prioritaria |
|----------------|------------------------------|
| Food, Restaurant | `restaurant` + keyword |
| Tree, Park | `park` + keyword |
| Church, Cathedral | `church` + landmark |
| Mountain, Lake | `tourist_attraction` |

## Manejo de OCR
- < 60 chars → Usar directamente como keyword
- ≥ 60 chars → Enviar a Ollama (phi3) para extracción de nombre
```

---

## 6. PROMPT: PostGIS + H3 Cache

```markdown
# GESTIÓN DE MEMORIA ESPACIAL (Level 1 Cache)

## Schema PostGIS

```sql
CREATE TABLE known_places (
  id SERIAL PRIMARY KEY,
  google_place_id VARCHAR(255) UNIQUE,
  display_name TEXT,
  place_type VARCHAR(100),
  geom GEOMETRY(Point, 4326),
  h3_index_res9 VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_h3 ON known_places(h3_index_res9);
CREATE INDEX idx_geom ON known_places USING GIST(geom);
CREATE INDEX idx_place_id ON known_places(google_place_id);
```

## Operations

### Find Match (Cache Hit)
```javascript
const query = `
  SELECT google_place_id, display_name, place_type,
         ST_X(geom) as lng, ST_Y(geom) as lat
  FROM known_places 
  WHERE h3_index_res9 = $1
  LIMIT 1;
`;
```

### Save Place (Cache Miss → Persist)
```javascript
const query = `
  INSERT INTO known_places (google_place_id, display_name, place_type, geom, h3_index_res9)
  VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326), $6)
  ON CONFLICT (google_place_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    updated_at = NOW();
`;
```

## TTL Strategy (Basado en Rover Case Study)
- TTL de 7 días es **conservador**
- Para datos geográficos, incluso 30 días es seguro
- Monitorear staleness con `updated_at`
```

---

## 7. PROMPT: Precision Benchmarks (Papers Académicos)

```markdown
# BENCHMARKS DE PRECISIÓN — Academia

## Estándares de Medición

### NSSDA (National Standard)
Usa RMSE con 95% de confianza para precisión posicional.

### Niveles de Precisión

| Nivel | Descripción | Precisión Típica |
|-------|-------------|------------------|
| Rooftop | "Estándar de oro" | ±10-50m |
| Address Point | Punto de dirección | ±15-30m |
| Street Interpolation | Interpolación de tramo | ±50-200m |
| ZIP Centroid | Centroide postal | ±500m-1km |

## Benchmarks por Entorno (USA)

| Entorno | Éxito Rooftop | Notas |
|---------|----------------|-------|
| Urbano | 70-90% | Mejor cobertura |
| Suburbano | 60-80% | Bueno |
| Rural | 40-60% | Datos limitados |

## Errores Comunes

### Interpolación Lineal (TIGER)
Produce errores >200m porque asume parcelas uniformes en una calle.

### Requisitos por Aplicación
- **Evaluación de riesgos de salud**: <50m
- **Clasificación de instalaciones**: <1500m
- **Tu sistema (fotos de usuario)**: ~11m (4 decimales)

## AI-Powered Solutions
Soluciones con IA afirman hasta **97% de precisión geométrica** vs 58% de industria.
```

---

## 8. PROMPT: Comparativa de Proveedores

```markdown
# COMPARATIVA DE PROVEEDORES 2026

## Google Maps Platform
| Aspecto | Detalle |
|---------|---------|
| **Fortalezas** | Cobertura 99.9%, precisión máxima, ecosistema integrado |
| **Debilidades** | $5/k req, prohibido almacenar, debe mostrar en mapa Google |
| **Ideal para** | Apps premium globales con presupuesto flexible |

## HERE Technologies
| Aspecto | Detalle |
|---------|---------|
| **Fortalezas** | Logística/automotive, límites de peso/altura, navegación 3D |
| **Debilidades** | Pricing complejo, compromisos de volumen |
| **Ideal para** | Gestión de flotas, rutas de entrega |

## Mapbox
| Aspecto | Detalle |
|---------|---------|
| **Fortalezas** | 100k req/mes gratis, personalización visual, 50-100ms respuesta |
| **Debilidades** | "Efecto acantilado": salto directo a $5/k sin rampas |
| **Ideal para** | Startups con UX diferenciador |

## OpenCage
| Aspecto | Detalle |
|---------|---------|
| **Fortalezas** | 2.5k req/día gratis, almacenamiento libre, GDPR, multi-fuente OSM |
| **Debilidades** | Precisión depende de comunidad OSM |
| **Ideal para** | Independencia de proveedores, investigación, presupuestos moderados |

## Geoapify
| Aspecto | Detalle |
|---------|---------|
| **Fortalezas** | 3k req/día gratis, fácil integración |
| **Debilidades** | Menos Enterprise-grade |
| **Ideal para** | Alternativa económica a Google Maps |

## Nominatim (OSM)
| Aspecto | Detalle |
|---------|---------|
| **Fortalezas** | Gratuito, open source, ilimitado (self-hosted) |
| **Debilidades** | API pública throttled, self-hosting costoso ($200-500/mes) |
| **Ideal para** | Prototipos, proyectos sin fines de lucro |

## Recomendación para tu Sistema
**Cascade**: OpenCage (N2) → Google Places (N3) → PostGIS H3 (N1)
```

---

## 9. PROMPT: Privacidad y Compliance (GDPR/HIPAA)

```markdown
# PRIVACIDAD Y COMPLIANCE

## HIPAA Compliance (USA)

### Requisitos Críticos
1. **BAA (Business Associate Agreement)**: Firmar con proveedor si procesas PHI
2. **SSL/HTTPS obligatorio**: Sin excepción para PHI
3. **Plan de Contingencia**: Respaldos y recuperación documentados

### OpenCage HIPAA
- ✅ Empresa alemana (GDPR compliant)
- ✅ Parámetro `no_record`: No guarda logs
- ✅ Retención de logs: 6 meses (o menos con no_record)
- ✅ BAA disponible en suscripciones Enterprise

## GDPR Compliance (EU)

### Principios Clave
1. **Minimización de datos**: Solo lo necesario
2. **Propósito específico**: No reutilizar para otros fines
3. **Derecho al olvido**: Capacidad de eliminar datos
4. **Consentimiento explícito**: Para cada tipo de procesamiento

## Privacy Mode (Anonimización)

```javascript
function anonymizeCoordinates(lat, lng, precision = 4) {
  const factor = Math.pow(10, precision);
  return {
    lat: Math.round(lat * factor) / factor,
    lng: Math.round(lng * factor) / factor
  };
}
```

### Niveles de Anonimización

| Precisión | Área Cubierta | Uso Recomendado |
|-----------|---------------|------------------|
| 2 decimales | ~1.1km | Agregación regional |
| 3 decimales | ~110m | Análisis urbano |
| 4 decimales | ~11m | **Tu sistema** |
| 5 decimales | ~1.1m | Ground truth (evitar) |

## Políticas de Retención

| Tipo de Dato | Retención | Justificación |
|--------------|-----------|---------------|
| Coordenadas GPS originales | 0 (inmediato) | Minimización |
| Coordenadas anonimizadas | 30 días | Caché |
| Nombres de lugares | Indefinido | Consentimiento |
| Metadatos EXIF (fecha) | 90 días | Auditoría opcional |
```

---

## 10. PROMPT: Manejo de Incertidumbre (Human-in-the-Loop)

```markdown
# VALIDACIÓN MANUAL — onConsensusFailure

## Detección de Fallo de Consenso

```javascript
const CONSENSUS_THRESHOLD = 0.75;

async function resolveWithConsensus(photos) {
  const consensus = calculateBatchConsensus(photos);

  if (consensus.score < CONSENSUS_THRESHOLD) {
    return {
      status: 'PENDING_HUMAN_VALIDATION',
      requiresManualValidation: true,
      validationToken: generateValidationToken(),
      uiPrompt: '¿Reconoces este lugar? Confirma o corrige.'
    };
  }

  return await persistResults(consensus);
}
```

## Estados de Validación

```javascript
const VALIDATION_STATES = {
  PENDING: { label: '⏳ Esperando validación', color: 'yellow' },
  CONFIRMED: { label: '✅ Validado', color: 'green', persist: true },
  CORRECTED: { label: '✏️ Corregido', color: 'blue', persist: true },
  REJECTED: { label: '❌ Rechazado', color: 'red', persist: false }
};
```

## Anti-Contaminación

```javascript
async function persistWithValidationCheck(result) {
  if (result.confidence < CONSENSUS_THRESHOLD) {
    const validation = await getValidationStatus(result.validationToken);
    
    if (validation.status !== 'CONFIRMED' && validation.status !== 'CORRECTED') {
      return null; // NO persistir sin validación
    }
  }
  await memoryStore.savePlace(result);
  return result;
}
```
```

---

## 11. PROMPT: Auditoría de Latencia y Rendimiento

```markdown
# MONITOREO DE RENDIMIENTO

## Objetivos de Latencia

| Nivel | Operación | Target | SLA |
|-------|-----------|--------|-----|
| N1 (Cache) | H3 Lookup | < 100ms | 99.9% |
| N2 (OpenCage) | Geocoding | < 800ms | 98% |
| N3 (Google) | Places API | < 500ms | 99% |

## Instrumentación

```javascript
class PerformanceAuditor {
  start(operation) { this.metrics.set(operation, performance.now()); }
  
  end(operation) {
    const duration = performance.now() - this.metrics.get(operation);
    console.log(`[PERF] ${operation}: ${duration.toFixed(2)}ms`);
    return duration;
  }
}

class ThroughputMonitor {
  constructor(windowMs = 60000) {
    this.requests = [];
    this.windowMs = windowMs;
  }
  
  record() { this.requests.push(Date.now()); this.cleanOld(); }
  
  getRPS() {
    this.cleanOld();
    return this.requests.length / (this.windowMs / 1000);
  }
  
  getStats() {
    const rps = this.getRPS();
    return {
      currentRPS: rps,
      alertThreshold: 50,
      isOverloaded: rps > 50
    };
  }
}
```

## Alertas

```javascript
const ALERT_RULES = [
  { name: 'HighLatency', condition: m => m.p95 > 500, severity: 'warning' },
  { name: 'CacheMissStorm', condition: m => m.hitRate < 0.5, severity: 'critical' },
  { name: 'BudgetBurn', condition: m => m.dailyCost > m.budget * 0.9, severity: 'critical' }
];
```

## Runbook de Escalación

| Nivel | Síntoma | Acción |
|-------|---------|--------|
| 🟡 L2 | p95 > 500ms | Revisar logs |
| 🟠 L3 | p99 > 1000ms | Escalar a DBA |
| 🔴 L4 | Servicio caído | Rollback |
| ☠️ L5 | Budget agotado | Shutdown no-críticos |
```

---

## 12. PROMPT: Selección de Proveedor según Caso de Uso

```markdown
# DECISION MATRIX — Selección de Provider

## Árbol de Decisión

```
¿Procesas datos de salud/PHI?
├─ SÍ → ¿Tienes BAA firmado?
│     ├─ SÍ → OpenCage (no_record) o Geocodio Enterprise
│     └─ NO → Solo datos anonimizados sin PHI
└─ NO → ¿Priorizas soberanía de datos?
        ├─ SÍ → OpenCage o Geoapify
        └─ NO → ¿Presupuesto limitado?
                ├─ SÍ → Mapbox (<100k) o Nominatim (self-hosted)
                └─ NO → Google Maps (máxima precisión)
```

## Guía Rápida de Selección

| Tu Situación | Provider Recomendado | Razón |
|--------------|---------------------|-------|
| Startup con UX diferenciador | Mapbox | 100k req gratis + personalización |
| App de consumo masiva | Google Maps | Máxima cobertura global |
| Logística y flotas | HERE | Datos especializados vehículos |
| Independencia de proveedores | OpenCage | Almacenamiento libre + GDPR |
| Budget muy limitado | Geoapify | 3k req/día gratis |
| Prototipo / hobby | Nominatim | Ilimitado self-hosted |
| Datos de salud (USA) | OpenCage + no_record | HIPAA compliant |
```

---

## APÉNDICE: Referencias Consultadas (NotebookLM)

### Pricing & Providers
- Radar: 15 best reverse geocoding tools
- AWS Marketplace: HERE Geocoding
- Zyla API Hub: Best Alternatives 2025
- Geocodio: Compare Geocoding Providers
- CSV2GEO: Geocoding API Pricing Compared 2026
- Geoapify: Geocoding Services Comparison
- Ambee: Google Geocoding API Alternative
- HERE Technologies: Official Pricing
- OpenCage: Official Pricing

### Academic & Case Studies
- PMC: Error propagation models in geocoding
- PubMed: Positional difference between geocoding methods
- arXiv: Building next-generation Geocoding systems
- Rover Search: Caching Reverse Geocoding at Scale

### Compliance & Privacy
- OpenCage: HIPAA compliant geocoding
- ArcGIS: Reverse Geocoding documentation
- LocationIQ: Geocodificación inversa

### Technical Documentation
- PostGIS: geocode and address standardization
- Nominatim: OpenStreetMap geocoder
- Mapbox: Geocoding API
- GeoPy: Documentation

---

*Documento generado desde NotebookLM → 49 fuentes consultadas*
*Versión: 2.0 | Fecha: 2026-04-14*
*Fuentes: Pricing 2026, Case Studies, Papers Académicos, Provider Comparisons, HIPAA Compliance*
