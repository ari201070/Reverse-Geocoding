# Skill: GoogleCloudSuite

Skill para la interacción optimizada con servicios de Google Cloud, centrada en el análisis visual y el geocoding inverso contextual.

## 🌐 APIs Críticas y Estado de Deshabilitación (OBLIGATORIO)

> [!IMPORTANT]
> **Riesgo Financiero Cero**: La variable `DISABLE_PAID_GOOGLE_APIS=true` indica de manera **obligatoria y estricta que todas las APIs de pago de Google están deshabilitadas**. No es opcional.
> - **Maps JavaScript API**: ❌ Deshabilitada y prohibida. Se utiliza **Leaflet + OpenStreetMap** de forma imperativa para el mapa interactivo del cliente.
> - **Places API (New) y Geocoding API**: ❌ Deshabilitadas y prohibidas. Las búsquedas de POIs y geocodificación inversa se resuelven exclusivamente mediante la cascada: **Caché Local -> Local Radius DB -> OpenCage**.
> - **Cloud Vision API**: ⚠️ Deshabilitada para procesamiento de pago de Google. En su lugar, se activa la cadena de modelos de visión gratuita (Free Vision LLM) y procesamiento OCR local.

## 🧠 Lógica de Búsqueda Contextual (Cascada Segura)

1.  **Detección de Señales**: Extraer etiquetas y OCR visuales mediante la cadena Free Vision LLM / modelos locales.
2.  **Sanitización OCR**: Utilizar **Ollama Cleanup** localmente para procesar y depurar textos OCR ruidosos antes de realizar búsquedas.
3.  **Búsqueda e Indexación H3**: Consultar la celda H3 Resolución 9 en la caché local o realizar una búsqueda espacial radial local.
4.  **Geocodificación de Respaldo**: Utilizar **OpenCage** (GDPR compliant, con parámetro `no_record=true`) si la caché local no contiene coincidencias.

## 🛡️ Manejo de Cuotas y Seguridad

- El frontend nunca debe intentar cargar el SDK script de Google Maps cuando `DISABLE_PAID_GOOGLE_APIS=true` está activo.
- Siempre proteger los tokens de OpenCage (`VITE_OPENCAGE_API_KEY`) y Picarta en `.env`.

