# SKILL-analysis: Análisis de Fisonomía y Sincronización Solar

## Objetivo
Validar la "Verdad del Lugar" mediante la extracción de evidencia física (arquitectura) y astronómica (sombras), eliminando la dependencia de APIs de nube para la verificación final y asegurando la Soberanía de Datos.

## Capacidades Core

### 1. Micro-Fisonomía Arquitectónica
Análisis de patrones estructurales y estéticos que definen la categoría y el uso del espacio.
- **Marcadores de Mobiliario:** Identificación de tipos de sillas, mesas y equipamiento específico (ej. máquinas de espresso, barras de bar).
- **Revestimientos:** Análisis de materiales en paredes, pisos y fachadas (ej. metal expandido, hormigón visto, madera tratada).
- **Categorización:** Clasificación en `Bodegón | Cafetería | Bar | Restaurante | Other` basada en la fisonomía.

### 2. Sincronización Solar (Solar Sync)
Validación geométrica de la ubicación mediante el análisis de la incidencia de luz y sombras.
- **Análisis de Sombras:** Determinación de la dirección (Azimut) y longitud de las sombras observadas en la imagen.
- **Contraste Teórico:** Comparación de la sombra observada vs. la posición teórica del sol para las coordenadas `{{lat}}, {{lng}}` y el tiempo `{{exifTime}}`.
- **Veredicto de Alineación:** 
    - `RECONSTRUCTED`: Las sombras coinciden con el modelo solar teórico.
    - `AMBIGUOUS`: Las sombras son inconsistentes o insuficientes para validar.
    - `REJECTED`: Las sombras contradicen la ubicación propuesta.

## Flujo de Razonamiento Local (Lógica para Ollama/Moondream)

Cuando el orquestador invoca esta skill, el agente debe seguir este proceso:

1. **Extracción de Evidencia Visual:**
   - Analizar la imagen buscando marcadores arquitectónicos únicos.
   - Identificar la fuente de luz dominante y la dirección de las sombras proyectadas.

2. **Cálculo de Coherencia:**
   - Recibir datos de tiempo y ubicación estimada.
   - Verificar si la dirección de la sombra es físicamente posible en ese punto geográfico a esa hora exacta.

3. **Sintetización de Evidencia:**
   - Combinar la categoría fisonómica con la validación solar.
   - Si la fisonomía sugiere un "Bar" y el sol confirma la ubicación, la confianza aumenta significativamente.

## Integración con el Orquestador (`resolve-puzzle.js`)

Esta skill se materializa a través de dos herramientas principales:
- `analyzeFisonomia`: Implementa la extracción de marcadores arquitectónicos.
- `analyzeSolarSync`: Implementa la validación astronómica de sombras.

## Guardrails de Soberanía
- **Procesamiento Local:** Todo el análisis de visión y razonamiento debe ocurrir en modelos locales (Moondream/Phi-3) para evitar la fuga de datos visuales a la nube.
- **Evidencia Física:** Priorizar siempre la evidencia física (sombras/materiales) sobre la semántica (nombres de lugares) en casos de ambigüedad.
