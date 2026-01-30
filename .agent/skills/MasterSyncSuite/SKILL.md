# Skill: MasterSyncSuite

Esta Skill encapsula las "Reglas Maestras" y la lógica de sincronización global para asegurar que todos los proyectos de la familia (Reverse-Geocoding, Viaje Familiar, etc.) funcionen de manera armonizada.

## 📜 Reglas de Desarrollo (Lean Agent)

Basado en `RULES_FOR_AI.md`:

- **Planning Primero**: Siempre generar un `implementation_plan.md` antes de codificar.
- **Eficiencia de Tokens**: Minimizar pasos de razonamiento y evitar bucles de autorreflexión.
- **Contexto bajo demanda**: Consultar archivos de reglas locales antes de realizar cambios estructurales.

## 🗝️ Gestión de API Keys (Guía Maestra)

Basado en `GUIA_API_KEYS.md`:

- **Consistencia de Nombres**: Usar `VITE_GOOGLE_API_KEY` para servicios de Mapas/Places.
- **Manejo Seguro**: Las claves deben residir en `.env` (no trackeado) con fallbacks configurados en Firebase si aplica.

## 🔄 Lógica de Sincronización (Firebase)

Basado en `EXPLICACION_SINCRONIZACION.md`:

- **Firestore**: Para metadatos de fotos (títulos, fechas, coordenadas) y listas (equipaje).
- **Storage**: Para los archivos binarios de las imágenes.
- **Auth**: Gestión de sesiones de usuario para asegurar que solo la familia acceda a los datos.

## 🌍 Bilingüismo y RTL

- **Estructura**: `locales/es.json` y `locales/he.json`.
- **Detección**: Persistencia en `localStorage`, layout dinámico (LTR/RTL) basado en `document.documentElement.dir`.
