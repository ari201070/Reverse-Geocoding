# Protocolo de Operación: Cascada GIS y Orquestación OSINT (V3.1)

## 1. Arquitectura de la Cascada de Resolución
El sistema utiliza una cascada de 5 niveles para determinar la "Verdad del Lugar" con costo cero (Zero-OPEX).

| Nivel | Componente | Tecnología | Latencia | Propósito |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | Caché Espacial | H3 Res 9 + PostGIS | 0.1ms | Resolución instantánea de lugares conocidos. |
| **L2** | FOSS Local | Photon / Overpass | < 50ms | Geocodificación sin salida a internet. |
| **L3** | **GeoPy Wrapper** | Python + RateLimiter | variable | Consultas masivas seguras a Nominatim/OSM. |
| **L4** | **Geoapify Tier** | `api/geoapify-handler.js` | ~200ms | Fallback de alta calidad (3k req/día gratis). |
| **L5** | OpenCage Tier | Cloud API | ~300ms | Último recurso de geocodificación comercial. |

---

## 2. El Veto de Velocidad (Física Pura)
Implementado en `scripts/geopy_consensus_orchestrator.py`, este protocolo impide errores de geocodificación mediante la validación de coherencia temporal:

- **Algoritmo:** Utiliza la distancia geodésica (GeoPy) entre dos fotos consecutivas.
- **Límite:** Si la velocidad requerida para el traslado supera los **120 km/h** (configurable), el sistema marca la ubicación como `AMBIGUOUS` y activa el Nivel 4.
- **Ecuación:** `v = geodesic_dist(p1, p2) / (t2 - t1)`.

---

## 3. Flujo de Escalamiento OSINT (Human-in-the-Loop)
Cuando el **Consensus Score < 0.75**, se activa el protocolo forense detallado en `MASTER_PROMPTS_V3_GIS_REVERSE_GEOCODING.md`:

1.  **Aislamiento:** El Orquestador identifica la señal débil (ej. OCR borroso o GPS inconsistente).
2.  **Preparación Visual:** Uso obligatorio de **GIMP (Corrección de Perspectiva)** para enderezar el plano de la imagen.
3.  **Búsqueda Inversa:** Consultas dirigidas a **TinEye** (píxeles exactos) o **Yandex** (patrones y texturas).
4.  **Cruce de Metadatos:** Verificación en bases de datos abiertas (Wikidata / Discogs).

---

## 4. Mantenimiento y Extensibilidad
- **Nuevos Handlers:** Cualquier nueva API debe seguir el patrón de `api/geoapify-handler.js` para asegurar la normalización de campos (`location_name`, `confidence`).
- **Lógica Python:** El script de Python debe mantenerse desacoplado, comunicándose con el backend de Node.js mediante la API local para evitar duplicidad de llaves API.

---
*Documento actualizado: 2026-07-14*
*Estado: Operativo*
