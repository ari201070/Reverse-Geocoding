# Skill: GoogleCloudSuite

Skill para la interacción optimizada con servicios de Google Cloud, centrada en el análisis visual y el geocoding inverso contextual.

## 🌐 APIs Críticas (Verificadas)

Esta skill utiliza las siguientes APIs habilitadas en la consola de Google Cloud:

- **Cloud Vision API**: Para detección de etiquetas y landmarks.
- **Places API (New)**: Búsqueda de POIs con soporte para keywords y campos detallados.
- **Geocoding API**: Fallback para direcciones postales exactas.
- **Maps JavaScript API**: Renderizado de interfaz interactiva.

## 🧠 Lógica de Búsqueda Contextual

1.  **Detección Vision**: Extraer el "top 3" de etiquetas visuales (ej: "montaña", "iglesia", "estadio").
2.  **Búsqueda Places**: Usar esas etiquetas como `keyword` en una búsqueda radial cerca de las coordenadas detectadas.
3.  **Filtrado de Resultados**: Priorizar `tourist_attraction`, `museum`, `park` y `establishment` sobre otros tipos genéricos.

## 🛡️ Manejo de Cuotas y Seguridad

- Siempre usar variables de entorno `VITE_GOOGLE_API_KEY`.
- Implementar cierres preventivos si la API retorna errores de cuota o autenticación.
