# Reverse Geocoding — App independiente

Este proyecto es una app web independiente que permite:

- Subir imágenes (extrae EXIF con exifr).
- Mostrar mapa con marcador y radio ajustable (Leaflet).
- Buscar POIs cercanos usando Google Places + Geocoding desde un endpoint serverless (/api/find-poi).
- Opciones de privacidad: consentimiento, anonimizar (redondeo), eliminar EXIF al exportar.

Estructura principal:

- index.html — UI
- src/app.js — lógica cliente
- src/styles.css — estilos
- api/find-poi.js — función serverless para Vercel que encapsula las llamadas a Google Maps APIs
- .env.example — ejemplo de variable de entorno

Requisitos:

- Node.js (para desarrollo con Vite)
- Cuenta en Google Cloud con habilitadas: Places API y Geocoding API
- Proyecto en Vercel (recomendado) para desplegar la función serverless y configurar la variable de entorno `GOOGLE_MAPS_API_KEY`.

Instalación y desarrollo local:

1. Clonar / crear carpeta y pegar archivos.
2. Instalar dependencias:
   npm install
3. Desarrollo local (frontend):
   npm run dev
   -> Abre http://localhost:5173

Probar la función serverless localmente (recomendado con Vercel CLI):

1. Instalar Vercel CLI:
   npm i -g vercel
2. Iniciar desarrollo que emula serverless:
   vercel dev
   -> Esto expondrá tanto el frontend como /api/find-poi localmente.
3. Configurar la variable de entorno en Vercel CLI o en .env (para `vercel dev` suele leer .env).

Despliegue en Vercel (sugerido):

1. Crear un nuevo proyecto en Vercel y conectar el repo.
2. En Settings → Environment Variables, agregar:
   - GOOGLE_MAPS_API_KEY = <tu clave>
3. Push a GitHub; Vercel hará build/deploy automáticamente. La función serverless quedará disponible en /api/find-poi.

Notas de privacidad y seguridad:

- La clave `GOOGLE_MAPS_API_KEY` debe guardarse en el backend (Vercel env vars). No expongas la clave en el frontend.
- Por defecto el endpoint realiza caché de resultados por coordenadas redondeadas (4 decimales) por 7 días para ahorrar cuota.
- La app ofrece redondeo/anonymize y strip-EXIF como opciones de privacidad.

Siguientes pasos recomendados:

- Si deseas reconocimiento visual (Vision API / Gemini Vision) y combinarlo con geocoding, implementa un endpoint backend separado que invoque Vision (no usar la API Key desde el cliente).
- Ajustar `POI_DISTANCE_THRESHOLD_M` según la precisión de tus fotos.
- Añadir limitación por usuario y logging si la app quedará pública.
