# Skill: ContextGeoIntegrator (Discovery Intelligence)

Esta skill es el cerebro del proyecto. Su misión es transformar una simple imagen en un lugar con nombre y contexto, superando las limitaciones del GPS tradicional.

## 🚀 Principio de "Vision-First Discovery"

El app debe ser "única e inteligente". No se limita a leer coordenadas; **entiende** lo que hay en la foto.

### 1. Jerarquía de Señales (Prioridad de Inteligencia)

Para encontrar un lugar, el sistema DEBE priorizar las señales en este orden:

1.  **LANDMARKS (Fuerte)**: Si Google Vision identifica una atracción turística o lugar famoso, ese es el nombre del lugar por defecto.
2.  **OCR (TEXT DETECCIÓN)**: Si hay un cartel con nombre (ej: "Aquafan", "La Farola"), ese texto es el término de búsqueda número 1.
3.  **VISUAL CONTEXT (LABELS)**: Si hay "Food", se priorizan restaurantes. Si hay "Tree", se priorizan parques.
4.  **EXIF/GEOLOCATION**: Las coordenadas sirven como ancla espacial, pero la visión define el contenido.

### 2. Reglas de Consenso "Cepa Pura" y Batch Awareness

El consenso no es solo una mayoría simple, es una **búsqueda de la verdad específica**:

- **REGLA DE ORO DE LOTE**: Si el usuario sube fotos en lote, el sistema DEBE asumir que se trata del mismo contexto geográfico. El procesamiento NO debe ser estrictamente secuencial; debe buscar "Pistas Maestras" (Landmarks/OCR) en cualquier foto del lote para aplicarlas al resto **antes** de recurrir a fallbacks lentos como Picarta.
- **Consenso de Vecindario**: Las fotos en un cluster (~100m, ~5min) DEBEN compartir keywords de visión. Si una foto tiene un Landmark, todas las búsquedas del cluster deben usar ese Landmark.
- **Puntuación Landmark-First**: Los nombres que contienen términos de lugares públicos (Jardín, Parque, Museo) tienen un peso multiplicador (x10) frente a negocios locales.
- **Propagación Agresiva**: Un nombre de alta calidad (Landmark detectado por AI) DEBE sobrescribir nombres genéricos o específicos de baja relevancia en todo el lote automáticamente.

### 3. Visual Evidence & Puzzle UI (Transparencia)

El sistema no debe ser una "caja negra". Debe visualizar su proceso de decisión:

- **Estrategia de Puzzle**: Mostrar el lote como piezas que se unen.
- **Anchor Photo**: Identificar visualmente la foto que proveyó la "Pista Maestra" (GPS/Landmark) con un borde o badge especial.
- **Badges de Evidencia**: Cada foto debe mostrar qué aportó al consenso (GPS, OCR, Hito Visual).
- **Nivel de Confianza**: Mostrar un % de certeza basado en la convergencia de pruebas.

## 🛡️ Estabilidad y Manejo de Errores (Master Patterns)

Para evitar fallos en lote y errores de ejecución:

- **Error Boundaries**: Toda ejecución de lógica compleja (Consenso, Picarta, Búsquedas) DEBE estar envuelta en bloques `try/catch`. Un error en un ítem o fase lógica NO debe detener el procesamiento de los demás archivos.
- **Idempotencia de Carga**: Librerías externas (Google Maps) deben cargarse una sola vez usando promesas persistentes para evitar `Uncaught ReferenceError`.
- **Validación de Ámbito**: No usar variables que dependan del contexto de una función hermana sin asegurar su retorno.

## 🛠️ Implementación Técnica

- **Backend (`find-poi.js`)**: Recibe `keywords`. Filtra nombres genéricos (calles) mediante `isGenericName` y aplica ranking por coincidencia de texto AI.
- **Frontend (`app.js`)**: Implementa `isGenericName` localmente. En procesamiento por lote, realiza una "Pasada de Señales Rápidas" (EXIF/Vision) en paralelo antes de la fase de filtrado y búsqueda profunda.
