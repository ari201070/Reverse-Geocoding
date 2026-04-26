# Guía de Programación: Ingeniería Inversa Geográfica

Este documento contiene información técnica detallada para implementar el sistema de reverse geocoding.

---

## 1. OCR con Google Cloud Vision API

### ¿Qué es OCR en este contexto?
OCR (Optical Character Recognition) en el sistema de Ingeniería Inversa Geográfica se usa para extraer texto legible de imágenes digitales. El texto detectado se convierte en la **"Huella Digital Semántica"** del lugar.

### Detección de Texto (Text Detection)

```javascript
// Ejemplo de llamada a Google Cloud Vision API
const vision = require('@google-cloud/vision');
const client = new vision.ImageAnnotatorClient();

// Detectar texto en imagen
const [result] = await client.textDetection('./imagen.jpg');
const detections = result.textAnnotations;

// El resultado incluye:
// - texto: El string completo detectado
// - boundingBox: Coordenadas del área de texto
// - confidence: Nivel de confianza (0-1)

console.log(detections[0].description); // Texto principal
console.log(detections[0].boundingPoly); // Box del texto completo
```

### Tipos de Detección

| Tipo | Descripción | Uso en el Sistema |
|------|-------------|-------------------|
| **Text Detection** | Extrae todo texto legible | **PRIMARIO** - Nombres de negocios, letreros |
| **Label Detection** | Identifica objetos/escenas | Categorización del lugar (restaurante, café) |
| **Landmark Detection** | Detecta monumentos/edificios famosos | Validación por hitos conocidos |
| **Logo Detection** | Detecta logotipos de marcas | Identificación de cadenas |

### Formato de Respuesta JSON

```json
{
  "textAnnotations": [
    {
      "description": "EL BOLICHE DE NICO",
      "boundingPoly": {
        "vertices": [
          {"x": 100, "y": 50},
          {"x": 300, "y": 50},
          {"x": 300, "y": 80},
          {"x": 100, "y": 80}
        ]
      },
      "confidence": 0.95
    },
    {
      "description": "BOLICHE",
      "boundingPoly": { ... },
      "confidence": 0.90
    }
  ]
}
```

### Manejo de Diferentes Tipos de Texto

| Tipo de Texto | Handling | Ejemplo |
|---------------|----------|---------|
| **Letreros comerciales** | Alta confianza, usar directamente | "El Boliche de Nico" |
| **Murals/Graffiti** | Requiere validación adicional | Dedicatorias Bochini |
| **Texto manuscrito** | Baja confianza, verificar con Fuzzy | "Para mi amigo Carlitos..." |
| **Textos pequeños** | Ignorar (probable ruido) | Números de calle |

### Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| Texto borroso | Movimiento de cámara | Verificar confidence > 0.7 |
| Reflejos/sobrescritura | Iluminación directa | Usar múltiples detecciones |
| Texto incompleto | Ángulo de cámara | Combinar con Label Detection |
| Idioma incorrecto | Configuración regional | Especificar hint de idioma |

---

## 2. RapidFuzz - Token Set Ratio

### ¿Qué es RapidFuzz?
Librería Python para fuzzy string matching (coincidencia difusa de strings). En el sistema se usa para **reconciliar** datos fragmentados.

### Algoritmo Token Set Ratio

```python
from rapidfuzz import fuzz

# Ejemplo de unificación de fragmentos
fragmento_1 = "Boliche"
fragmento_2 = "Nico"

# Token Set Ratio: Convierte strings a sets de tokens
# y calcula similitud basándose en intersección
resultado = fuzz.token_set_ratio(fragmento_1, fragmento_2)
print(resultado)  # Ejemplo: 60 (0-100)

# Unificación práctica
def unificar_nombre(fragmentos):
    # Encontrar la mejor combinación de fragmentos
    mejor_match = None
    mejor_score = 0
    
    for i in range(len(fragmentos)):
        for j in range(i+1, len(fragmentos)):
            combinacion = f"{fragmentos[i]} {fragmentos[j]}"
            score = fuzz.token_set_ratio(combinacion, "El Boliche de Nico")
            if score > mejor_score:
                mejor_score = score
                mejor_match = combinacion
    
    return mejor_match, mejor_score

# Ejemplo práctico:
# "Boliche" + "Nico" → "Boliche Nico" → score: 75% match
```

### Cómo Funciona el Algoritmo

1. **Tokenización**: Divide strings en tokens individuales
   - "El Boliche de Nico" → ["el", "boliche", "de", "nico"]

2. **Ordenamiento**: Ordena tokens alfabéticamente
   - ["boliche", "de", "el", "nico"]

3. **Conjuntos**: Convierte a sets y calcula intersección/union
   - set1 = {"boliche", "de", "el", "nico"}
   - set2 = {"boliche", "nico"}

4. **Score**: 2 * |intersección| / |set1| + |set2|

### Parámetros Importantes

```python
# score_cutoff: Retorna None si el score es menor al umbral
fuzz.token_set_ratio("Boliche", "Nico", score_cutoff=50)  # None si < 50

# threshold para considerarse "match válido"
UMBRAL_MATCH = 70  # 70% de similitud mínimo

# partial_ratio: Para strings muy cortos dentro de largos
fuzz.partial_ratio("Nico", "El Boliche de Nico")  # 100 (encuentra "Nico" dentro)
```

### Uso en el Sistema

```python
# Pseudocódigo de reconciliación
def reconciliar_nombre(texto_detectado, base_datos_lugares):
    resultados = []
    
    for lugar in base_datos_lugares:
        score = fuzz.token_set_ratio(
            texto_detectado.upper(), 
            lugar['nombre'].upper()
        )
        
        if score >= UMBRAL_MATCH:
            resultados.append({
                'lugar': lugar,
                'score': score
            })
    
    # Ordenar por score descendente
    resultados.sort(key=lambda x: x['score'], reverse=True)
    return resultados
```

---

## 3. H3 - Índice Espacial Hexagonal

### ¿Qué es H3?
Sistema de índices geoespaciales desarrollado por Uber. Divide la Tierra en celdas hexagonales jerárquicas.

### Resolución y Precisión

| Resolución | Área Celda | Uso |
|-------------|------------|-----|
| 7 | ~163 km² | País/Estado |
| 8 | ~21 km² | Ciudad grande |
| **9** | **~0.87 km² (~11m)** | **Local/Barrio** ← ESTÁNDAR |
| 10 | ~0.12 km² (~40m) | Intersección |
| 11 | ~0.018 km² (~15m) | Edificio |

### Integración con PostGIS

```sql
-- Habilitar extensión H3
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS h3;

-- Tabla de lugares con índice H3
CREATE TABLE lugares (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    lat DECIMAL(10, 8),
    lon DECIMAL(11, 8),
    h3_index BIGINT,  -- índice H3 resolución 9
    confianza DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Crear índice GiST para búsquedas espaciales
CREATE INDEX idx_lugares_h3 ON lugares USING GIST(h3_index);

-- Convertir lat/lon a H3
INSERT INTO lugares (nombre, lat, lon, h3_index)
VALUES (
    'El Boliche de Nico',
    -34.6037,
    -58.3816,
    h3_lat_lng_to_cell(-34.6037, -58.3816, 9)  -- Retorna: 892834akerfffff
);

-- Buscar lugares en celda H3 específica
SELECT * FROM lugares 
WHERE h3_index = h3_lat_lng_to_cell(-34.6037, -58.3816, 9);

-- Buscar lugares en celda y sus vecinas
SELECT * FROM lugares 
WHERE h3_index IN (
    h3_grid_disk(h3_lat_lng_to_cell(-34.6037, -58.3816, 9), 1)
);
```

### B-Tree vs GiST para PostGIS

| Tipo | Uso | Ventaja |
|------|-----|---------|
| **B-Tree** | Equality queries (=) | Más rápido para búsquedas exactas |
| **GiST** | Range queries (>, <, BETWEEN) | Necesario para búsquedas por proximidad |

```sql
-- B-Tree (recomendado para H3 con igualdad)
CREATE INDEX idx_h3_btree ON lugares USING btree(h3_index);
-- Tiempo para 1M registros: ~0.1ms

-- GiST (para búsquedas por distancia)
CREATE INDEX idx_h3_gist ON lugares USING gist(h3_geo_to_h3(geom));
-- Tiempo para 1M registros: ~50ms
```

### Consulta Completa de Ejemplo

```sql
-- Encontrar todos los lugares a ~11m de coordenadas
-- equivale a celda H3 resolución 9
WITH target_cell AS (
    SELECT h3_lat_lng_to_cell(-34.6037, -58.3816, 9) as h3
)
SELECT 
    l.nombre,
    ST_Distance(
        ST_Point(-58.3816, -34.6037)::geography,
        ST_Point(l.lon, l.lat)::geography
    ) as distancia_m
FROM lugares l, target_cell t
WHERE l.h3_index = t.h3
ORDER BY distancia_m;
```

---

## 4. Foto Ancla - Definición y Proceso

### ¿Qué Define una Foto como Ancla?

Una foto se convierte en **Foto Ancla** cuando cumple:

```
Ancla = (OCR_EXITO) O (LANDMARK_DETECTADO)
```

Donde:
- **OCR_EXITO**: Texto detectado con confidence >= 0.7 Y nombre válido encontrado en base de datos
- **LANDMARK_DETECTADO**: Landmark con MID (Machine Identifier) Y confidence >= 0.8

### Proceso Completo de Validación

```python
class FotoAncla:
    def __init__(self, foto):
        self.foto = foto
        self.datos = {}
    
    def validar(self) -> bool:
        # 1. Intentar OCR
        ocr_resultado = self._ejecutar_ocr()
        
        if ocr_resultado['success']:
            # 2. Verificar en base de datos
            match = self._buscar_en_db(ocr_resultado['texto'])
            if match and match['score'] >= 70:
                self.datos = match
                return True
        
        # 3. Intentar Landmark
        landmark_resultado = self._detectar_landmark()
        
        if landmark_resultado['success']:
            if landmark_resultado['confidence'] >= 0.8:
                self.datos = landmark_resultado
                return True
        
        return False
    
    def _ejecutar_ocr(self):
        # Llamar a Google Cloud Vision
        return {
            'success': True,
            'texto': 'EL BOLICHE DE NICO',
            'confidence': 0.95
        }
    
    def _detectar_landmark(self):
        # Llamar a Landmark Detection
        return {
            'success': True,
            'landmark_id': 'ChIJxxx...',
            'nombre': 'Boliche de Nico',
            'confidence': 0.85
        }
```

### Datos Almacenados cuando una Foto se Convierte en Ancla

```python
datos_ancla = {
    'foto_id': 'uuid-foto-123',
    'es_ancla': True,
    'metodo_validacion': 'OCR',  # o 'LANDMARK'
    'datos_validacion': {
        'texto_detectado': 'EL BOLICHE DE NICO',
        'confidence': 0.95,
        'lugar_id': 'place-123',
        'nombre_lugar': 'El Boliche de Nico',
        'coordenadas': {
            'lat': -34.603722,
            'lon': -58.381589
        },
        'h3_index': 892834akerfffff,
        'bounding_box': {...}
    },
    'timestamp': '2026-04-15T20:00:00Z',
    'score_confianza': 0.95
}
```

### Propagación a Fotos Relacionadas

```python
def propagar_desde_ancla(foto_ancla, fotos_lote):
    """Propaga datos de ancla a otras fotos del lote"""
    
    fotos_heredadas = []
    
    for foto in fotos_lote:
        if foto.id == foto_ancla.id:
            continue
            
        # Verificar condiciones de herencia
        tiempo_diff = abs(foto.timestamp - foto_ancla.timestamp)
        misma_celda = foto.h3_index == foto_ancla.h3_index
        
        if tiempo_diff <= 900 and misma_celda:  # 15 min = 900s
            foto.heredar_datos(foto_ancla.datos)
            fotos_heredadas.append(foto)
    
    return fotos_heredadas
```

---

## 5. Herencia - Condiciones y Propagation

### Condiciones Exactas para Herencia

```
HERENCIA = (tiempo_diff <= 15min) Y (misma_celda_H3_res9)
```

| Condición | Valor | Notas |
|-----------|-------|-------|
| **Tiempo** | <= 15 minutos (900 segundos) | Diferencia entre timestamps EXIF |
| **Espacio** | Misma celda H3 Res 9 | ~170m de diámetro |

### Código de Verificación

```python
def puede_heredar(foto_candidata, foto_ancla) -> bool:
    # 1. Verificar tiempo
    tiempo_diff = abs(
        foto_candidata.exif_timestamp - foto_ancla.exif_timestamp
    ).total_seconds()
    
    if tiempo_diff > 900:  # 15 minutos
        return False, "Tiempo > 15 minutos"
    
    # 2. Verificar espacio (misma celda H3)
    if foto_candidata.h3_index != foto_ancla.h3_index:
        return False, "Celdas H3 diferentes"
    
    # 3. Verificar que ancla tenga datos válidos
    if not foto_ancla.datos_validacion:
        return False, "Ancla sin datos"
    
    return True, "Herencia válida"

# Uso
es_valida, razon = puede_heredar(foto_candidata=foto_2, foto_ancla=foto_1)
if es_valida:
    print("Herencia aplicada")
else:
    print(f"Herencia denegada: {razon}")
```

### Datos que se Heredan

```python
datos_heredados = {
    # Coordenadas de la foto ancla
    'lat': foto_ancla.lat,
    'lon': foto_ancla.lon,
    
    # Índice espacial
    'h3_index': foto_ancla.h3_index,
    
    # Identificación del lugar
    'lugar_id': foto_ancla.lugar_id,
    'nombre_lugar': foto_ancla.nombre_lugar,
    
    # Metadatos de validación
    'metodo_origen': foto_ancla.metodo_validacion,
    'confianza_origen': foto_ancla.score_confianza,
    
    # Propagación
    'heredado_de': foto_ancla.foto_id,
    'heredado_en': datetime.now()
}
```

### Casos donde NO se Aplica Herencia

| Escenario | Comportamiento |
|-----------|----------------|
| Foto > 15 min después del ancla | No hereda, requiere validación propia |
| Foto en celda H3 diferente | No hereda, proceso independiente |
| Foto ancla con baja confianza (<0.5) | Foto ancla no válida, no propaga |
| Foto sin EXIF timestamp | No hereda (no se puede verificar tiempo) |
| Primera foto del lote (sin ancla) | Se intenta validar como ancla |

### Manejo de Anclas con Baja Confianza

```python
def procesar_foto_baja_confianza(foto):
    """Cuando ancla tiene score bajo, usar validación reforzada"""
    
    if foto.ancla and foto.ancla.score_confianza < 0.5:
        # No信任 immediately, requerir validación humana
        foto.marcar_pendiente_revision()
        
        # O intentar múltiples métodos de validación
        metodos = [
            validar_por_ocr(),
            validar_por_landmark(),
            validar_por_micro_fisonomia()
        ]
        
        # Usar el de mayor confianza
        mejor_metodo = max(metodos, key=lambda x: x['confidence'])
        
        if mejor_metodo['confidence'] >= 0.7:
            foto.actualizar_datos(mejor_metodo)
        
    return foto
```

---

## 6. Algoritmo de Consenso - Scoring Ponderado

### Tabla de Pesos

| Señal | Peso | Condición |
|-------|------|-----------|
| **OCR** | 0.8 | Texto detectado con confidence >= 0.7 |
| **Landmark** | 0.8+ | Landmark con confidence > 0.8 (extras por confianza > 0.9) |
| **Micro-fisonomía** | 0.3-0.6 | Según cantidad de objetos detectados |

---

## 8. MICRO-FISONOMÍA - Memoria Visual del Lugar

### El Concepto Fundamental

La **Micro-fisonomía** es el análisis de elementos visuales最小的 que definen la identidad de un lugar más allá de coordenadas GPS o nombres comerciales. Es lo que hace que un lugar sea único y reconocible: el tipo de sillas, el color del mantel, la pintura de las paredes, el estilo del bar.

**¿Por qué es importante?**
- GPS puede decirte que estás en una coordenada específica
- Pero NO puede decirte si el local cambió de nombre o si la fachada cambió pero el interior se conserva
- Múltiples usuarios subiendo fotos desde diferentes ángulos construyen un **puzzle visual colectivo**

### Elementos Visuales Detectados

La IA utiliza **Label Detection** de Google Cloud Vision para detectar objetos y categorías:

```javascript
// Respuesta de Label Detection
const labels = [
  { description: "Table", score: 0.95 },
  { description: "Chair", score: 0.89 },
  { description: "Restaurant", score: 0.85 },
  { description: "Tablecloth", score: 0.78 },
  { description: "Wall", score: 0.72 },
  { description: "Bar", score: 0.68 },
  { description: "Window", score: 0.65 },
  { description: "Lighting", score: 0.55 }
];
```

### Catálogo de Elementos por Categoría

| Categoría | Elementos |
|-----------|-----------|
| **Mobiliario** | Tipo de sillas (madera, metal, cuero), mesas (redondas, cuadradas), manteles (color, tela), banquetas |
| **Paredes** | Color de pintura, tipo de revestimiento (ladrillo, madera, empapelado), decoraciones, espejos |
| **Bar/Counter** | Material (madera, mármol, acero), altura, taburetes, estantes de bebidas |
| **Iluminación** | Tipo de lamparas (colgantes, araña, aplique), intensidad, temperatura de color |
| **Señalética** | Carteles internos, menus, pizarras,人均 |
| **Detalles** | Macetas, cuadros, fotografías, banderines, objetos decorativos |

### Ejemplo: Diferenciación de Tipos de Establecimiento

```
Restaurante Formal:
├── Sillas: Cuero oscuro, acolchadas
├── Mesas: Rectangulares, mantel blanco
├── Paredes: Pintura oscura, cuadros framados
├── Bar: Americano, largo, mármol
└── Iluminación: Cálida, tenue

Café/Bar de Barrio:
├── Sillas: Plástico colores, simples
├── Mesas: Redondas, sin mantel
├── Paredes: Azulejos,挂在锅
├── Bar: Corto, madera
└── Iluminación: Fluorescente, brillante

Bodegón:
├── Sillas: Madera frailero, oscuras
├── Mesas: Plywood, individuales
├── Paredes: Chapa verde/celeste
├── Bar: Mesada baja,冰箱
└── Iluminación: Combination tube/bulb
```

### Construcción de la "Memoria Visual" Colectiva

```python
class MemoriaVisual:
    """Sistema que construye memoria visual de un lugar a través del tiempo"""
    
    def __init__(self, lugar_id):
        self.lugar_id = lugar_id
        self.elementos = {}  # nombre -> [observaciones]
    
    def agregar_observacion(self, foto, labels_detectados):
        """Agregar nueva observación de una foto"""
        
        timestamp = foto.exif_timestamp
        
        for label in labels_detectados:
            if label.score >= 0.6:  # Umbral de confianza
                if label.description not in self.elementos:
                    self.elementos[label.description] = []
                
                self.elementos[label.description].append({
                    'timestamp': timestamp,
                    'score': label.score,
                    'angulo': foto.angulo_camara,
                    'foto_id': foto.id
                })
    
    def construir_perfil(self):
        """Construir perfil visual consolidado del lugar"""
        
        perfil = {}
        
        for elemento, observaciones in self.elementos.items():
            # Ordenar por score
            observaciones.sort(key=lambda x: x['score'], reverse=True)
            
            # Conservar los mejores elementos (evitar ruido)
            mejores = observaciones[:10]  # Top 10
            
            perfil[elemento] = {
                'presencia': len(observaciones),
                'confianza_promedio': sum(o['score'] for o in mejores) / len(mejores),
                'primera_vez': min(o['timestamp'] for o in observaciones),
                'ultima_vez': max(o['timestamp'] for o in observaciones),
                'angulos_vistos': list(set(o['angulo'] for o in observaciones))
            }
        
        return perfil
```

### Ejemplo de Evolución Temporal

```
LUGAR: "El Boliche de Nico" (lugar_id: place-123)

FASE 1 (2024-01): Usuario A sube foto del interior
├── Elementos detectados: ["Chair", "Table", "Tablecloth", "Wall"]
├── Perfil inicial: Sillas madera, mantel a cuadros, paredes verdes
└── Estado: 4 elementos, confianza 0.72

FASE 2 (2024-06): Usuario B sube foto desde otra mesa
├── Nuevos elementos: ["Bar", "Window", "Beer"]
├── Perfil actualizado: +3 elementos, confianza 0.75
└── Confirmación: Mismos elementos de Fase 1 + bar de madera

FASE 3 (2025-02): Usuario C sube foto del mostrador
├── Nuevos elementos: ["Cash register", "Phone", "Clock"]
├── Perfil consolidado: 10+ elementos, confianza 0.85
└── Estado: Perfil visual completo del lugar

FASE 4 (2025-08): Usuario D sube foto - FACHADA CAMBIÓ
├── Externo: ["Storefront", "Signage"] (NUEVO NOMBRE)
├── Interno: ["Chair", "Table"] (MISMO INTERIOR)
├── Deducción: Local cambió nombre pero mismo negocio
└── Acción: Mantener ID lugar, actualizar OCR para nuevo nombre
```

### Manejo: Fachada Cambió pero Interior se Conserva

```python
def detectar_cambio_fachada(lugar_existente, foto_nueva):
    """Detectar si cambió la fachada pero interior se mantiene"""
    
    # 1. Obtener perfil visual histórico
    perfil_existente = lugar_existente.perfil_visual
    
    # 2. Analizar elementos de foto nueva
    elementos_nuevos = foto_nueva.labels
    
    # 3. Comparar
    elementos_interior = ['Chair', 'Table', 'Bar', 'Wall', 'Tablecloth']
    elementos_fachada = ['Storefront', 'Signage', 'Door', 'Awning']
    
    match_interior = 0
    for elem in elementos_interior:
        if elem in elementos_nuevos:
            match_interior += 1
    
    match_fachada = 0
    for elem in elementos_fachada:
        if elem in elementos_nuevos:
            match_fachada += 1
    
    # 4. Decisión
    if match_interior >= 3 and match_fachada >= 1:
        #可能有 cambio de fachada pero mismo interior
        return {
            'mismo_lugar': True,
            'cambio_fachada': True,
            'evidencia': {
                'match_interior': match_interior,
                'match_fachada': match_fachada,
                'recomendacion': 'Actualizar nombre pero mantener lugar_id'
            }
        }
    
    return {'mismo_lugar': False}
```

### Almacenamiento en Base de Datos

```sql
-- Tabla de memoria visual por lugar
CREATE TABLE lugar_memoria_visual (
    id SERIAL PRIMARY KEY,
    lugar_id TEXT REFERENCES lugares(id),
    
    -- Elementos visuales detectados (JSON)
    elementos JSONB,
    
    -- Timestamps de primera/última observación
    primera_observacion TIMESTAMP,
    ultima_observacion TIMESTAMP,
    
    -- Metadata de construcción
    fotos_usadas INTEGER DEFAULT 0,
    score_confianza DECIMAL(3, 2),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índice para búsqueda rápida
CREATE INDEX idx_lugar_memoria ON lugar_memoria_visual USING GIN(elementos);
```

### Score de Micro-fisonomía en el Algoritmo de Consenso

```python
def calcular_score_micro_fisonomia(foto, lugar_existente):
    """Calcular cuánto contribuyen los elementos visuales al score"""
    
    if not lugar_existente.memoria_visual:
        return 0.0, "Sin memoria visual previa"
    
    elementos_foto = set(l.description for l in foto.labels)
    elementos_lugar = set(lugar_existente.memoria_visual.elementos.keys())
    
    # Calcular overlap
    совпадения = elementos_foto & elementos_lugar
    
    if not совпадения:
        return 0.0, "Sin match con memoria existente"
    
    # Score basado en cuántos elementos coinciden
    # + bonus por nuevos elementos que enriquecen la memoria
    score_base = len(совпадения) / len(elementos_foto) if elementos_foto else 0
    
    # Pesos por tipo de elemento (los más distintivos tienen más peso)
    peso_mobiliario = 0.3
    peso_decoracion = 0.2
    peso_iluminacion = 0.1
    
    score_final = min(0.6, score_base * 1.5)  # Cap at 0.6
    
    return score_final, f"Match: {len(совпадения)}/{len(elementos_foto)} elementos"
```

### Beneficios del Sistema de Memoria Visual

1. **Resistencia a cambios**: Si Google Maps no actualiza, el sistema detecta el lugar por su interior
2. **Multi-user collaboration**: Cada usuario aporta un piece del puzzle
3. **Evolución temporal**: El lugar puede cambiar pero el sistema documenta la transformación
4. **Desambiguación**: Dos locales en misma calle se diferencian por interior único
5. **Recuperación de historial**: Fotos antiguas muestran cómo era el lugar antes
| **GPS** | 0.2 | Siempre disponible pero menos preciso |

### Cálculo de Score Final

```python
def calcular_score(foto) -> float:
    score = 0.0
    total_peso = 0.0
    
    # OCR
    if foto.ocr_result:
        peso = 0.8 * foto.ocr_result.confidence
        score += peso
        total_peso += 0.8
    
    # Landmark
    if foto.landmark_result:
        peso = 0.8 + (foto.landmark_result.confidence - 0.8)
        score += peso
        total_peso += 0.8
    
    # Micro-fisonomía
    if foto.objetos_detectados:
        peso = min(0.6, len(foto.objetos_detectados) * 0.1)
        score += peso
        total_peso += 0.6
    
    # GPS (siempre cuenta pero con peso bajo)
    if foto.gps_coordenadas:
        score += 0.2
        total_peso += 0.2
    
    # Normalizar a porcentaje
    return (score / total_peso) * 100 if total_peso > 0 else 0
```

### Thresholds de Decisión

```python
THRESHOLD_AUTOMATICO = 75  # Porcentaje
THRESHOLD_BAJO = 50        # Requiere revisión

def decision_final(score):
    if score >= THRESHOLD_AUTOMATICO:
        return "APROBADO_AUTOMATICO"
    elif score >= THRESHOLD_BAJO:
        return "REVISION_HUMANA"
    else:
        return "RECHAZADO"
```

---

## 7. Fallback en Cascada (3 Niveles)

```python
def geocodificar(foto):
    # Nivel 1: Caché Local (PostGIS)
    resultado = buscar_en_cache(foto.h3_index)
    if resultado:
        return resultado, "CACHE"
    
    # Nivel 2: Google Places API
    resultado = buscar_en_google(foto)
    if resultado:
        guardar_en_cache(resultado)
        return resultado, "GOOGLE"
    
    # Nivel 3: OpenCage
    resultado = buscar_en_opencage(foto)
    if resultado:
        guardar_en_cache(resultado)
        return resultado, "OPENCAGE"
    
    return None, "FALLO_TOTAL"
```

---

## 9. FOTO ANCLA - Sistema Completo de Anchoring

### Concepto Fundamental

La **Foto Ancla** es la piedra angular del sistema de geocodificación inversa. Es la primera foto de un lote que se resuelve exitosamente y sirve como referencia para propagar ubicación a todas las demás fotos del conjunto.

**Analogía del Puzzle**: Es como la pieza central de un rompecabezas - una vez que identificas una pieza, puedes ubicar todas las piezas circundantes.

### Condiciones Exactas para Convertirse en Ancla

```python
# Threshold de confianza
OCR_MIN_CONFIDENCE = 0.7      # 70% mínimo para OCR
LANDMARK_MIN_CONFIDENCE = 0.8 # 80% mínimo para Landmark
FUZZY_MIN_SCORE = 70           # 70% mínimo en RapidFuzz

def puede_ser_ancla(foto) -> bool:
    """Determina si una foto puede ser ancla"""
    
    # Método 1: OCR exitoso
    if foto.ocr_resultado:
        if foto.ocr_resultado['confidence'] >= OCR_MIN_CONFIDENCE:
            # Verificar fuzzy match con base de datos
            match = buscar_en_db(foto.ocr_resultado['texto'])
            if match and match['score'] >= FUZZY_MIN_SCORE:
                return True, 'OCR'
    
    # Método 2: Landmark detectado
    if foto.landmark_resultado:
        if foto.landmark_resultado['confidence'] >= LANDMARK_MIN_CONFIDENCE:
            return True, 'LANDMARK'
    
    return False, None
```

### Prioridad entre Múltiples Candidatas

Cuando múltiples fotos del lote podrían ser ancla, el sistema prioriza:

```python
def seleccionar_mejor_ancla(candidatas) -> FotoAncla:
    """Selecciona la mejor foto para ser ancla"""
    
    # Ordenar por prioridad:
    # 1. Mayor confidence de OCR/Landmark
    # 2. Tipo: LANDMARK > OCR (más confiable)
    # 3. Menor timestamp (más temprana)
    
    def calcular_prioridad(foto):
        base_score = foto.confidence
        
        # Bonus por tipo
        tipo_bonus = {
            'LANDMARK': 0.2,
            'OCR': 0.0
        }.get(foto.metodo_validacion, 0)
        
        return base_score + tipo_bonus
    
    candidatas.sort(key=calcular_prioridad, reverse=True)
    
    return candidatas[0]
```

### Datos Almacenados por Ancla

```python
class FotoAnclaData:
    foto_id: str              # UUID único de la foto
    lote_id: str              # ID del lote/sesión de fotos
    es_ancla: bool            # Flag indicating es ancla
    
    metodo_validacion: str    # 'OCR' | 'LANDMARK' | 'MICRO_FISONOMIA'
    metodo_confidence: float  # 0.0 - 1.0
    
    datos_reconocimiento: {    # Para OCR:
        'texto_detectado': str,
        'texto_normalizado': str,
        'bounding_boxes': list,
        'match_en_db': {
            'lugar_id': str,
            'nombre_oficial': str,
            'fuzzy_score': float
        }
    }
    
    ubicacion: {
        'lat': float,
        'lon': float,
        'h3_index': bigint,
        'precision_metros': float
    }
    
    temporal: {
        'exif_timestamp': datetime,
        'created_at': datetime,
        'source': str
    }
    
    score: {
        'confianza_final': float,
        'peso_ocr': float,
        'peso_landmark': float,
        'peso_micro_fisonomia': float
    }
```

### Almacenamiento en Base de Datos

```sql
CREATE TABLE fotos_anclas (
    id SERIAL PRIMARY KEY,
    foto_id TEXT NOT NULL UNIQUE,
    lote_id TEXT NOT NULL,
    es_ancla BOOLEAN DEFAULT TRUE,
    metodo_validacion TEXT NOT NULL,
    metodo_confidence DECIMAL(3, 2) NOT NULL,
    datos_reconocimiento JSONB NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,
    lon DECIMAL(11, 8) NOT NULL,
    h3_index BIGINT NOT NULL,
    precision_metros DECIMAL(6, 2),
    exif_timestamp TIMESTAMP,
    source TEXT DEFAULT 'USER_UPLOAD',
    confianza_final DECIMAL(3, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_anclas_lote ON fotos_anclas(lote_id);
CREATE INDEX idx_anclas_h3 ON fotos_anclas(h3_index);

CREATE TABLE herencia_fotos (
    id SERIAL PRIMARY KEY,
    foto_ancla_id TEXT NOT NULL REFERENCES fotos_anclas(foto_id),
    foto_heredada_id TEXT NOT NULL,
    tiempo_diff_seconds INTEGER NOT NULL,
    misma_celda_h3 BOOLEAN NOT NULL,
    lat DECIMAL(10, 8),
    lon DECIMAL(11, 8),
    h3_index BIGINT,
    lugar_id TEXT,
    nombre_lugar TEXT,
    heredado_en TIMESTAMP DEFAULT NOW(),
    UNIQUE(foto_heredada_id)
);
```

### Proceso Completo de Propagación (Herencia)

```python
class SistemaHerencia:
    MAX_TIEMPO_HERENCIA = 900   # 15 minutos en segundos
    USAR_CELDA_VECINA = True
    
    def procesar_lote(self, fotos, foto_ancla):
        resultados = {
            'ancla': foto_ancla,
            'heredadas': [],
            'sin_herencia': []
        }
        
        for foto in fotos:
            if foto.id == foto_ancla.id:
                continue
            
            es_valida, razon = self.verificar_herencia(foto, foto_ancla)
            
            if es_valida:
                datos_heredados = self.aplicar_herencia(foto, foto_ancla)
                foto.asignar_datos(datos_heredados)
                resultados['heredadas'].append(foto)
            else:
                foto.requiere_validacion_propia = True
                resultados['sin_herencia'].append({'foto': foto, 'razon': razon})
        
        return resultados
    
    def verificar_herencia(self, foto_candidata, foto_ancla):
        tiempo_diff = abs(
            (foto_candidata.exif_timestamp - foto_ancla.exif_timestamp).total_seconds()
        )
        
        if tiempo_diff > self.MAX_TIEMPO_HERENCIA:
            return False, f"超过15min ({tiempo_diff}s)"
        
        if foto_candidata.h3_index != foto_ancla.h3_index:
            if self.USAR_CELDA_VECINA:
                if not self.es_celda_vecina(foto_candidata.h3_index, foto_ancla.h3_index):
                    return False, "Celdas H3 diferentes"
            else:
                return False, "Celdas H3 diferentes"
        
        if not foto_ancla.tiene_datos_validos():
            return False, "Ancla sin datos válidos"
        
        return True, "Herencia válida"
    
    def aplicar_herencia(self, foto_heredada, foto_ancla):
        return {
            'lat': foto_ancla.lat,
            'lon': foto_ancla.lon,
            'h3_index': foto_ancla.h3_index,
            'lugar_id': foto_ancla.lugar_id,
            'nombre_lugar': foto_ancla.nombre_lugar,
            'metodo_origen': foto_ancla.metodo_validacion,
            'confianza_origen': foto_ancla.confianza_final,
            'heredado_de': foto_ancla.foto_id,
            'heredado_en': datetime.now(),
            'tipo_herencia': 'ANCLA_PRIMARIA'
        }
```

### Manejo de Anclas con Baja Confianza

```python
class GestorAnclasBajaConfianza:
    CONFIANZA_BAJA = 0.5
    CONFIANZA_REVISION = 0.7
    
    def procesar_ancla_baja_confianza(self, foto_ancla, fotos_lote):
        if foto_ancla.confianza_final < self.CONFIANZA_BAJA:
            foto_ancla.marcar_pendiente_revision()
            return {'usar_como_ancla': False, 'razon': 'Confianza muy baja', 'accion': 'REQUIERE_REVISION_HUMANA'}
        
        elif foto_ancla.confianza_final < self.CONFIANZA_REVISION:
            foto_ancla.marcar_requiere_verificacion()
            return {'usar_como_ancla': True, 'razon': 'Confianza media', 'accion': 'PROPAGAR_CON_VERIFICACION', 'verificar_despues': True}
        
        return {'usar_como_ancla': True, 'razon': 'Confianza adecuada', 'accion': 'PROPAGAR_NORMAL'}
```

### Casos Edge y Cómo Manejarlos

| Escenario | Manejo |
|-----------|--------|
| Sin fotos válidas en lote | Crear ancla vacía, cada foto requiere validación propia |
| Múltiples anclas posibles | Seleccionar por mayor confianza, otras quedan como backup |
| Ancla con baja confianza | No propagar, requerir revisión humana |
| Primera foto del lote sin OCR/Landmark | Intentar micro-fisonomía como fallback |
| Fotos en diferentes celdas H3 | Cada celda tiene su propio ancla |
| Ancla muy antigua (más de 1 año) | Revalidar antes de usar para propagación |

### Métricas y Monitoreo

```sql
SELECT metodo_validacion, COUNT(*) as total
FROM fotos_anclas
GROUP BY metodo_validacion;

SELECT 
    CASE 
        WHEN confianza_final >= 0.9 THEN 'ALTA'
        WHEN confianza_final >= 0.7 THEN 'MEDIA'
        ELSE 'BAJA'
    END as nivel,
    COUNT(*) as total
FROM fotos_anclas
GROUP BY nivel;

SELECT 
    COUNT(DISTINCT hf.foto_heredada_id) as fotos_heredadas,
    COUNT(DISTINCT fa.foto_id) as total_anclas,
    ROUND(
        COUNT(DISTINCT hf.foto_heredada_id)::numeric / 
        COUNT(DISTINCT fa.foto_id)::numeric * 100, 2
    ) as tasa_herencia
FROM fotos_anclas fa
LEFT JOIN herencia_fotos hf ON fa.foto_id = hf.foto_ancla_id;
```

### Beneficios del Sistema de Anclas

1. **Ahorro de API calls**: Una llamada OCR sirve para 5-10 fotos
2. **Velocidad**: Herencia es casi instantánea (~0.1ms)
3. **Consistencia**: Fotos del mismo lugar comparten coordenadas exactas
4. **Resiliencia**: Si falla OCR en foto B, puede heredar de foto A
5. **Costo**: 80-90% ahorro en costos de geocodificación

**Benefits del Sistema de Anclas**

1. **Ahorro de API calls**: Una llamada OCR sirve para 5-10 fotos
2. **Velocidad**: Herencia es casi instantánea (~0.1ms)
3. **Consistencia**: Fotos del mismo lugar comparten coordenadas exactas
4. **Resiliencia**: Si falla OCR en foto B, puede heredar de foto A
5. **Costo**: 80-90% ahorro en costos de geocodificación

---

## 10. IMPLEMENTACIÓN REAL vs DOCUMENTACIÓN

### Comparativa: Sistema Documentado vs Código Fuente

Esta sección alinea la teoría con el código real en `src/utils/puzzleLogic.js` y `api/resolve-puzzle.js`.

### Sistema de Scoring del Código

```javascript
// De api/resolve-puzzle.js - Phase 1: Weighted Anchor Ranking

const scoredPhotos = photos.map(p => {
    let score = 0;
    let bestToken = null;
    let pType = 'NONE';

    // 1. Landmark (Master Clue) - 1.0
    const landmark = p.visionLabels?.find(l => l.isLandmark);
    if (landmark) {
        score = 1.0;
        bestToken = landmark.name;
        pType = 'LANDMARK';
    } 
    // 2. Short OCR (<60 characters) - 0.8
    else if (p.ocrText && p.ocrText.trim().length > 3 && p.ocrText.trim().length < 60) {
        score = 0.8;
        bestToken = p.ocrText.trim();
        pType = 'OCR_SHORT';
    }
    // 3. Long OCR / Ollama Required - 0.4
    else if (p.ocrText && p.ocrText.trim().length >= 60) {
        score = 0.4;
        bestToken = p.ocrText.trim();
        pType = 'OCR_LONG';
    }
    // 4. GPS Only - 0.2
    else if (p.lat && p.lng) {
        score = 0.2;
        pType = 'GPS_ONLY';
    }

    return { ...p, score, bestToken, type: pType };
});
```

### Tabla de Pesos Reales

| Tipo | Score | Longitud OCR | Notas |
|------|-------|-------------|-------|
| **LANDMARK** | 1.0 | N/A | Master clue - isLandmark=true |
| **OCR_SHORT** | 0.8 | < 60 chars | Mejor resultado |
| **OCR_LONG** | 0.4 | >= 60 chars | Requiere Ollama cleanup |
| **GPS_ONLY** | 0.2 | N/A | Fallback |
| **NONE** | 0.0 | N/A | Requiere validación |

### Tie-Breaker: GPS Accuracy

```javascript
// De api/resolve-puzzle.js - Rule: Lowest Accuracy is the secondary sort key
const sortedAnchors = scoredPhotos
    .filter(p => p.score > 0)
    .sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        return a.accuracy - b.accuracy; // Tie-break: lowest accuracy meters first
    });
```

### Temporal Windows del Código

```javascript
// De src/utils/puzzleLogic.js
const TIME_WINDOW_S = 3600;      // 60 minutos: clustering
const INHERIT_WINDOW_S = 900;   // 15 minutos: herencia
const H3_RESOLUTION = 9;          // ~170m hexágonos
```

### Clustering y Herencia

```javascript
// De src/utils/puzzleLogic.js
function finalizeCluster(photos) {
    const anchor = pickAnchor(photos);

    if (anchor && anchor.lat != null) {
        for (const p of photos) {
            if (p.lat == null && p.lng == null) {
                const diff = Math.abs(p.timestamp - anchor.timestamp) / 1000;
                if (diff <= INHERIT_WINDOW_S) {  // 15 min
                    p.lat = anchor.lat;
                    p.lng = anchor.lng;
                    p.inherited = true;
                    p.inheritanceSource = anchor.id;
                }
            }
        }
    }
}
```

### UI: PuzzleSummary.js

El componente UI (`src/components/PuzzleSummary.js`) muestra:

```javascript
// Roles de fotos en UI
img.role === 'ANCHOR_VISUAL'  // Mostrar badge "ANCLA"

// Badges indicadores
img.exif?.has_gps           // GPS disponible
img.vision_analysis?.landmark // Landmark detectado
img.vision_analysis?.ocr_text // OCR exitoso
```

### Cálculo de Confianza

```javascript
// De api/resolve-puzzle.js
const anchorScore = masterAnchor?.score || 0.1;
const consistencyBonus = results.filter(r => r.name && r.name === results[0]?.name).length / results.length;
const finalConfidence = Math.min(0.99, (anchorScore * 0.7) + (consistencyBonus * 0.3));

// Threshold: 75% para automático
requiresManualValidation: finalConfidence < 0.75
```

### Flujo Completo del Sistema

```
1. fotos[] → phase1: WEIGHTED ANCHOR RANKING (score 0.2-1.0)
            │
            ▼
2. masterAnchor = sortedAnchors[0] + tie-breaker accuracy
            │
            ▼
3. phase2: OLLAMA CLEANUP (solo para OCR_LONG >= 60 chars)
            │
            ▼
4. phase3: SPATIAL MEMORY lookup (si hay coords sin nombre)
            │
            ▼
5. phase4: CLUSTER & PROPAGATION (< 15 min inheritance)
            │
            ▼
6. Calculate confidence = (anchorScore * 0.7) + (consistency * 0.3)
            │
            ▼
7. Return: confidence < 75% ? MANUAL_VALIDATION : AUTO
```

### Endpoints del API

| Endpoint | Descripción |
|----------|------------|
| POST /api/resolve-puzzle | Batch consensus con anchoring |
| POST /api/analyze-image | Cloud Vision (labels, landmarks, texts) |
| GET /api/memory | Spatial memory lookup |

---

## Resumen de Configuración Recomendada

```python
# Configuración del sistema
CONFIG = {
    # Scoring
    'landmark_score': 1.0,
    'ocr_short_score': 0.8,
    'ocr_long_score': 0.4,
    'gps_only_score': 0.2,
    
    # OCR
    'ocr_short_threshold_chars': 60,
    'ocr_confidence_min': 0.7,
    
    # Fuzzy matching
    'fuzzy_score_min': 70,
    
    # Temporal windows
    'cluster_window_seconds': 3600,    # 60 min clustering
    'inherit_window_seconds': 900,     # 15 min inheritance
    
    # H3
    'h3_resolucion': 9,              # ~170m
    'h3_precision_metros': 11,      # 4 decimales
    
    # Consenso
    'confidence_automatico_min': 0.75,  # 75%
    'confidence_revision_min': 0.50,     # 50%
    
    # Ponderación final
    'peso_anchor_confidence': 0.7,
    'peso_consistencia': 0.3
}
```

---

*Documento generado: 2026-04-15*
*Fuente: Código real + NotebookLM - Sistema v3.2*