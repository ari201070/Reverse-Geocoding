# 🗝️ Guía Maestra de API Keys - Proyecto Familias Viajeras

Este documento aclara la función de cada clave, dónde se encuentra y cómo se configura para evitar confusiones en el futuro.

## 1. Google Cloud / Google Maps API Key

**Nombre en el proyecto:** `VITE_GOOGLE_API_KEY`
**Ubicación:** `.env` (Raíz del proyecto)
**Función:**

- Proporciona servicios de **Geocoding Inverso** (convertir coordenadas de fotos en nombres de lugares como "Mendoza" o "VIP Rosario").
- Se usa en el archivo: `src/utils/photoMetadata.ts`.
  **Configuración Crítica:**
- Debe estar habilitada la **"Geocoding API"** y la **"Places API" (New)** en la consola de Google Cloud.
- Por seguridad, en el código se usa un "fail-safe" que busca esta clave primero en el entorno (`import.meta.env`) y luego en las credenciales de Firebase como respaldo.

---

## 2. Firebase API Key (Browser Key)

**Nombre en el proyecto:** `apiKey`
**Ubicación:** `src/firebaseCredentials.ts`
**Función:**

- Identifica la aplicación ante los servicios de **Firebase** (Authentication, Firestore, Storage).
- Es la "llave" para que el usuario pueda hacer Login y que la base de datos acepte cambios.
  **Configuración Crítica:**
- Se obtiene de la consola de Firebase -> Configuración del proyecto -> Tus Apps.
- **API Key:** Termina en `...iREQ`.
- **Project ID:** `viajes-argentina-en-30-dias`
- **Messaging Sender ID:** `52421464497`
- **App ID:** `1:52421464497:web:f0b3465b9492afa97bad90` (Configurada para viajes-argentina-en-30-dias).

---

## 3. Gemini AI / Polygon API Key

**Nombres en el proyecto:** `GEMINI_API_KEY` o `API_KEY` (Genérica)
**Ubicación:** `.env` y `vite.config.mjs`
**Función:**

- `GEMINI_API_KEY`: Para las funciones de Inteligencia Artificial que analizan el itinerario.
- `POLYGON_API_KEY` (opcional): Para tasas de cambio de moneda en tiempo real.
  **Configuración Crítica:**
- Vite las inyecta a través del bloque `define` en `vite.config.mjs` para que el navegador pueda verlas.

---

## 4. Resumen de Archivos de Configuración

| Archivo                      | Propósito                               | Manejo de Seguridad                                                   |
| :--------------------------- | :-------------------------------------- | :-------------------------------------------------------------------- |
| `.env`                       | Almacena claves locales (VITE\_...).    | **NO** se sube a GitHub (está en `.gitignore`).                       |
| `src/firebaseCredentials.ts` | Configuración estática de Firebase.     | Contiene la clave de Firebase por conveniencia de deploy.             |
| `vite.config.mjs`            | Puente entre el sistema y el navegador. | Configura el prefijo `VITE_` y expone variables al `import.meta.env`. |

---

## Próximos Pasos (Para retomar el proyecto)

Si el geocoding deja de funcionar o la consola dice "MISSING API KEY":

1. Verificar que el archivo `.env` exista y tenga la clave.
2. Reiniciar el servidor con `npm run dev` (Vite no lee cambios de `.env` en caliente).
3. Verificar permisos en Google Cloud Console para la clave específica.
