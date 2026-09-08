# Skill: Extracción Visual (OCR & Landmarks)

## Objetivo
Identificar textos únicos y landmarks arquitectónicos usando Google Cloud Vision API.

## Herramientas
- **Google Cloud Vision API**:
  - TEXT_DETECTION: Extraer texto de imágenes
  - LANDMARK_DETECTION: Detectar monumentos/edificios famous
  - LABEL_DETECTION: Identificar objetos (mobiliario, categoría)

## Prioridad de Detección

| Tipo | Score | Longitud OCR | Uso |
|------|-------|-------------|------|
| **LANDMARK** | 1.0 | N/A | Master clue - alta confianza |
| **OCR_SHORT** | 0.8 | < 60 chars | Mejor resultado |
| **OCR_LONG** | 0.4 | >= 60 chars | Requiere cleanup con Ollama |
| **GPS_ONLY** | 0.2 | N/A | Fallback |

## Proceso

### 1. Text Detection
- Extraer todo texto legible de la imagen
- Detectar murales, dedicatorias, letreros comerciales
- Devolver bounding boxes y confidence score

### 2. Landmark Detection
- Identificar monumentos/edificios conocidos
- Usar MID (Machine Identifier) para reconciliación
- Alta prioridad en el sistema de anchoring

### 3. Label Detection
- Identificar categoría del lugar (restaurante, café, etc.)
- Detectar mobiliario (sillas, mesas,etc.)
- Construir perfil visual del lugar

## Código de Referencia

```javascript
// De api/analyze-image.js
const features = [
    { type: 'LABEL_DETECTION', maxResults: 15 },
    { type: 'LANDMARK_DETECTION', maxResults: 5 },
    { type: 'TEXT_DETECTION', maxResults: 5 }
];
```

## th de Respuesta

```json
{
    "labels": ["Restaurant", "Table", "Chair"],
    "landmarks": ["Teatro Colón"],
    "texts": ["EL BOLICHE DE NICO"]
}
```

## References
- [5] Reconciliación con RapidFuzz
- [6] Micro-fisonomía