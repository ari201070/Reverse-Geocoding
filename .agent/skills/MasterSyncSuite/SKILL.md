# Skill: MasterSyncSuite

Esta Skill encapsula las "Reglas Maestras" y la lógica de sincronización global para asegurar que todos los proyectos de la familia (Reverse-Geocoding, Viaje Familiar, etc.) funcionen de manera armonizada.

## 📜 Reglas de Desarrollo (Lean Agent)

El núcleo de comportamiento del agente reside en los recursos internos del skill:

- **[RULES_FOR_AI.md](file:///C:/Users/flier/.gemini/antigravity/scratch/Reverse-Geocoding/.agent/skills/MasterSyncSuite/resources/RULES_FOR_AI.md)**: Estrategia de tokens, modo lean y protocolos de procesamiento.
- **[GLOBAL_AI_SETUP.md](file:///C:/Users/flier/.gemini/antigravity/scratch/Reverse-Geocoding/.agent/skills/MasterSyncSuite/resources/GLOBAL_AI_SETUP.md)**: Configuración del IDE y la plataforma.

## 🗝️ Gestión de API Keys (Guía Maestra)

- **[GUIA_API_KEYS.md](file:///C:/Users/flier/.gemini/antigravity/scratch/Reverse-Geocoding/.agent/skills/MasterSyncSuite/resources/GUIA_API_KEYS.md)**: Consistencia en nombres (ej. `VITE_GOOGLE_API_KEY`) y manejo seguro en `.env`.

## 🔄 Lógica de Sincronización (Firebase)

- **[EXPLICACION_SINCRONIZACION.md](file:///C:/Users/flier/.gemini/antigravity/scratch/Reverse-Geocoding/.agent/skills/MasterSyncSuite/resources/EXPLICACION_SINCRONIZACION.md)**: Estrategia para migrar de `localStorage` a Firestore/Storage asegurando persistencia multi-dispositivo.

## 🌍 Bilingüismo y RTL

- **Estructura**: `locales/es.json` y `locales/he.json`.
- **Detección**: Persistencia en `localStorage`, layout dinámico (LTR/RTL) basado en `document.documentElement.dir`.
