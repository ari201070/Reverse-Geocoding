# Ingeniería Inversa Geográfica - Recursos de Desarrollo

## Las 6 Respuestas Completas

---

### 1. Flujo de Trabajo Completo

La ingeniería inversa geográfica reconstruye la "Verdad del Lugar" mediante **4 pilares fundamentales**:

1. **Huella Digital Semántica (OCR e Inferencia)**
   - Cuando no hay coordenadas precisas, usa texto del entorno como identificador único
   - OCR (Google Cloud Vision) para digitalizar textos manuscritos/murales
   - Búsqueda en Knowledge Graph de Google para vincular foto con locales
   - Reconciliación con RapidFuzz (Token Set Ratio)

2. **Análisis de Micro-fisonomía y Contexto Visual**
   - Inferir ubicación basándose en entorno físico (sin letreros)
   - Categorización por objetos (mobiliario, revestimientos)
   - Detección de Hitos (Landmarks) con MID oficial

3. **Sincronización Temporal**
   - Fotos dentro de 15 minutos comparten contexto geográfico
   - Herencia de ubicación entre fotos del mismo lote

4. **SpatialCache (PostGIS + H3)**
   - Base de datos propia de lugares conocidos
   - Consultas optimizadas con índices hexagonales

---

### 2. H3 con Orientación del Dispositivo

**Resolución 9** (~11m precisión) como ancla espacial:
- Define el "punto de origen" o celda desde la cual se captura la imagen
- Filtra inmediatamente POIs en esa celda hexagonal o vecinas

**Refinamiento mediante el "Apuntado":**
- Orientación del dispositivo = filtro direccional sobre datos espaciales
- **Landmark-First**: priorizar hitos en la línea de visión del usuario
- Análisis de Micro-fisonomía confirma si objetos detectados coinciden con ubicación teórica

**Eficiencia en SpatialCache:**
- H3 B-Tree: **0.1ms** para 1M lugares (vs 1500ms trigonométrico = **15,000x más rápido**)

---

### 3. Foto Ancla en Modo Puzzle

**Definición:** Imagen dentro de un lote que ha sido "resuelta" exitosamente (OCR/landmark detectado).

**Herencia de Ubicación:**
Las demás fotos del lote heredan coordenadas si:
- < 15 minutos de diferencia respecto al ancla
- Misma celda H3 Resolución 9 (~170 metros)

**Ahorro Operativo (OPEX):**
- Resolver solo la "verdad" de una imagen y propagarla
- **80-90% de ahorro** en costos de geocodificación

---

### 4. Algoritmo de Consenso

**Scoring Ponderado:**
| Señal | Peso |
|-------|------|
| OCR de alta autoridad (letreros/murales) | 0.8 |
| Hitos (Landmarks) con confianza >0.8 | 0.8+ |
| Análisis de Micro-fisonomía | Variable |
| Señal GPS | 0.2 (más débil) |

**Thresholds (Umbrales):**
- **Consenso automático**: >75% de confianza
- **Bloqueo de seguridad**: si reconciliación semántica (RapidFuzz) falla

**Lógica de Fallback (Cascada 3 niveles):**
1. **Nivel 1**: Caché Local (PostGIS)
2. **Nivel 2**: Google Places API
3. **Nivel 3**: OpenCage

**Validación Humana:** Si score < 75% → requiresManualValidation

---

### 5. Métricas de Precisión

**Por Nivel (Benchmarks Estándar):**
| Nivel | Precisión |
|-------|-----------|
| Rooftop (oro) | ±10-50m |
| Address Point | ±15-30m |
| Tu Sistema (4 decimales) | ~11m |
| Street Interpolation | ±50-200m (evitar) |

**Por Entorno:**
| Entorno | Éxito | Error |
|---------|-------|-------|
| Urbano | 70-90% | ±15-50m |
| Suburbano | 60-80% | ±50-100m |
| Rural | 40-60% | ±200m |

**Benchmarks de Rendimiento:**
- H3 B-Tree: 0.1ms para 1M lugares
- Método tradicional: 1500ms para 1M lugares

---

### 6. Compliance y Privacidad

**Anonimización:**
- **4 decimales** (~11m) = estándar de seguridad
- **5+ decimales** (~1.1m) = **PROHIBIDO** (permite identificar domicilio)
- **Difuminado direccional**: desplazar vector de visión en registros públicos

**Políticas de Retención:**
| Tipo de Dato | Retención |
|--------------|-----------|
| GPS original | 0 (eliminación inmediata) |
| GPS anonimizado (4 decimales) | 30 días |
| Metadatos EXIF (fecha/orientación) | 90 días |
| Nombres de lugares | Indefinido (con consentimiento) |

**Requisitos HIPAA/Técnicos:**
- BAA obligatorio con proveedores
- Cifrado SSL/HTTPS
- Parámetro `no_record` en APIs externas

**Soberanía de Datos:**
- GDPR (OpenCage = empresa alemana)
- SpatialCache propia (PostGIS) - control total sobre datos

---

## INFOGRAFÍA: Prompt para Generación

```
Crea una infografía profesional sobre "Ingeniería Inversa Geográfica: Reconstrucción de la Verdad del Lugar"

ESTRUCTURA:

1. TÍTULO PRINCIPAL (arriba)
   "Ingeniería Inversa Geográfica"
   Subtítulo: "Cómo reconstruir la ubicación exacta a partir de fotos"

2. SECCIÓN 1: Los 4 Pilares (cuadrante superior izquierdo)
   - Icono: Lente de OCR
     Texto: "Huella Digital Semántica"
     Descripción: OCR + Knowledge Graph + RapidFuzz
   - Icono: Ojo
     Texto: "Micro-fisonomía Visual"
     Descripción: Objetos + mobiliário + landmarks
   - Icono: Reloj
     Texto: "Sincronización Temporal"
     Descripción: Fotos < 15 min heredan ubicación
   - Icono: Base de datos
     Texto: "SpatialCache"
     Descripción: PostGIS + H3

3. SECCIÓN 2: H3 + Orientación (cuadrante superior derecho)
   Diagrama:
   - Hexágono H3 (resolución 9, ~11m)
   - Flecha desde centro representando "orientación del dispositivo"
   - POIs filtrados en la dirección de la flecha
   - Label: "Landmark-First: priorizar hitos en línea de visión"

4. SECCIÓN 3: Foto Ancla - Modo Puzzle (cuadrante inferior izquierdo)
   Diagrama de flujo:
   [Foto Ancla] → Herencia si: (<15min + misma celda H3)
   → [Fotos del Lote] → [80-90% ahorro en costos]

5. SECCIÓN 4: Algoritmo de Consenso (cuadrante inferior derecho)
   Scoring:
   - OCR: 0.8 ★★★★★
   - Landmark: 0.8+ ★★★★★
   - Micro-fisonomía: variable ★★★★
   - GPS: 0.2 ★
   
   Threshold: >75% = automático
   Fallback: Cache → Google → OpenCage
   Validación humana si <75%

6. FOOTER: Métricas y Privacidad
   - Precisión: Rooftop ±10-50m, tu sistema ~11m
   - Velocidad: H3 B-Tree 0.1ms (15,000x más rápido)
   - Privacidad: 4 decimales = ~11m (seguro)
   - Prohibido: 5+ decimales (identifica domicilio)

ESTILO:
- Colores: Azul técnico (#2563EB), Verde éxito (#16A34A), Naranja acento (#F97316)
- Tipografía: Sans-serif moderna
- Iconos: Minimalistas, línea fina
- Fondo: Blanco con grids sutiles
```

---

## CUESTIONARIO: 10 Preguntas de Opción Múltiple

### Pregunta 1
**¿Cuál es la precisión aproximada de las coordenadas con 4 decimales?**
- a) ~1 metro
- b) ~11 metros ✓
- c) ~50 metros
- d) ~100 metros

### Pregunta 2
**¿Qué resolución H3 se usa como estándar en el sistema?**
- a) Resolución 7 (~5km²)
- b) Resolución 8 (~0.74km²)
- c) Resolución 9 (~0.11km² = ~11m) ✓
- d) Resolución 10 (~15,824m²)

### Pregunta 3
**¿Cuánto tiempo puede pasar entre una foto ancla y las fotos que heredan su ubicación?**
- a) 5 minutos
- b) 15 minutos ✓
- c) 30 minutos
- d) 1 hora

### Pregunta 4
**¿Cuál es el peso (score) del OCR de alta autoridad en el algoritmo de consenso?**
- a) 0.2
- b) 0.5
- c) 0.8 ✓
- d) 1.0

### Pregunta 5
**¿Qué umbral de confianza se requiere para geocodificación automática?**
- a) >50%
- b) >75% ✓
- c) >90%
- d) 100%

### Pregunta 6
**¿Cuántas veces más rápido es H3 B-Tree vs método trigonométrico para 1M lugares?**
- a) 100x
- b) 1,000x
- c) 15,000x ✓
- d) 150,000x

### Pregunta 7
**¿Por qué está prohibido usar 5+ decimales en coordenadas?**
- a) Costoso
- b) Lento
- c) Permite identificar domicilio exacto ✓
- d) No hay diferenciación

### Pregunta 8
**¿Cuál es la retención de GPS anonimizado (4 decimales)?**
- a) Inmediato (0 días)
- b) 30 días ✓
- c) 90 días
- d) Indefinido

### Pregunta 9
**¿Qué proveedor garantiza cumplimiento nativo de GDPR?**
- a) Google Maps
- b) Mapbox
- c) OpenCage ✓
- d) Apple Maps

### Pregunta 10
**¿Cuál es el primer nivel en la cascada de fallback del sistema?**
- a) Google Places API
- b) OpenCage
- c) Caché Local (PostGIS) ✓
- d) GPS directo

---

## TIMELINE: Proceso de Geocodificación Inversa

```
FASE 1: CAPTURA (Input)
├── Foto capturada con GPS
├── EXIF: fecha, hora, coordenadas
└── Orientación del dispositivo (opcional)

        ↓
        
FASE 2: EXTRACCIÓN (Cascading Priority)
├── Nivel 1: EXIF nativo (lat/lon)
├── Nivel 2: XMP (Adobe/Google Photos)
├── Nivel 3: IPTC Core
└── Nivel 4: Fallback Visual (Picarta AI)

        ↓
        
FASE 3: PROCESAMIENTO (Spatial Index)
├── Calcular índice H3 Resolución 9
├── Verificar Caché Local (PostGIS)
│   └── HIT → retornar lugar cacheado
└── MISS → continuar a siguiente nivel

        ↓
        
FASE 4: ANÁLISIS (Evidencia Visual)
├── Cloud Vision API
│   ├── OCR (texto detectado)
│   ├── Label Detection (objetos)
│   └── Landmark Detection (hitos)
├── Scoring ponderado
│   ├── OCR: 0.8
│   ├── Landmark: 0.8+
│   └── Micro-fisonomía: variable
└── GPS: 0.2 (más débil)

        ↓
        
FASE 5: CONSENSO (Validación)
├── Calcular confianza final
├── ¿Score >= 75%?
│   ├── SI → Geocodificación automática
│   └── NO → Validación humana requerida
└── RapidFuzz para reconciliación semántica

        ↓
        
FASE 6: PERSISTENCIA (SpatialCache)
├── Guardar en PostGIS
├── Indexar con H3 Resolución 9
├── Actualizar biblioteca de lugares conocidos
└── Listo para siguientes consultas

        ↓
        
FASE 7: HERENCIA (Modo Puzzle)
├── Si foto reciente (<15min, misma celda H3)
├── Hereda ubicación de foto ancla
├── No requiere nueva consulta API
└── 80-90% ahorro en costos
```

---

*Documento generado: 2026-04-15*
*Fuente: NotebookLM - reverse-geocoding-docs-3*