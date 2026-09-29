# Auditoría de Infraestructura de Vecindad y Preparación del Lote de Roma — Tempio di Portuno

**Fecha:** 2026-09-28
**Objetivo:** Reutilizar caché y desambiguación espacio-temporal existente para `Tempio di Portuno; Roma; Italia;` sin duplicar scripts ni falsos positivos.

---

## 1. Mapeo y Análisis de Lógica de Tránsito (`apps/frontend/api/`)

### `geojson-cache.js` — Indexación y Levante en Memoria `apps/frontend/api/geojson-cache.js:1`

| Función | Ubicación | Descripción exacta |
|---|---|---|
| `loadWorldGeoJson()` | `:40` | Carga `FeatureCollection` mundial desde `spatial-utils.js` (fichero local, no API). |
| Filtro `bbox` | `:42-60` | Si `req.query.bbox=minLng,minLat,maxLng,maxLat`, filtra `worldGeoJson.features` por intersección de `feature.bbox` (rectángulo). Si no hay `bbox`, retorna todos los países. Inyecta `properties.source='LOCAL_COUNTRY_BOUNDARIES'` para Leaflet. |
| `known_places` PostGIS | `:82-102` | `SELECT place_id, name, anon_latitude, anon_longitude, confidence_score, h3_res9, place_data FROM known_places WHERE review_status='RECONSTRUCTED' ORDER BY created_at DESC`. Mapea cada fila a `Feature Point [lng,lat]` con `source='LOCAL_CACHE_POSTGIS'`. |
| Fallback | `:119` | Si `pool` no existe o query falla, sirve solo `countryFeatures` y loguea `warn`, no rompe endpoint. |
| Combinación | `:125` | `combinedFeatures = [...databaseFeatures, ...countryFeatures]` y `res.json({type:'FeatureCollection', features: combinedFeatures})`. |

**Reutilizable para Tempio di Portuno:** No tocar. El tag `Tempio di Portuno` cae en `known_places` como punto `RECONSTRUCTED` con `h3_res9`. `geojson-cache.js` ya lo sirve filtrado por `bbox` de Roma (12.45-12.50,41.88-41.92) sin costo adicional. Radio de cobertura de los datasets (ver §2) es el `bbox` del `Feature`.

### `resolve-puzzle.js` — Orquestador Batch Consensus `apps/frontend/api/resolve-puzzle.js:1`

| Parámetro / Regla | Valor exacto | Ubicación | Uso para Tempio |
|---|---|---|---|
| `H3_RESOLUTION` | `9` (~170 m lado, ~0.06 km²) | `:76` | Misma celda para fotos contiguas del Foro Boario. Tempio `12.4830,41.8895` -> `h3=891e805...` (ver datasets). |
| `INHERIT_WINDOW_MS` | `15 * 60 * 1000` (15 min) | `:77` | Herencia temporal estricta: solo fotos con `|t_curr - t_anchor| <=15 min` heredan. |
| `calculateDistance` | Haversine `R=6371` | `:104` | Valida veto cinemático. |
| `HIGH_RELEVANCE_KEYWORDS` | 80+ términos ES/EN `catedral, plaza, museo, monumento, templo, tempio, foro boario` | `:81` | `Tempio di Portuno` puntúa x10 por `templo/tempio`. |
| `rankAnchors` | `LANDMARK 1.0 > OCR_SHORT 0.8 > OCR_LONG 0.4 > GPS_ONLY 0.2`, desempate `gpsAccuracy` | `:584` | Prioriza ancla con `landmark:isLandmark=true` para Tempio. |
| `INHERIT_WINDOW` extendida | `60.0 min` en `migrate-to-postgres.js:92` (no en resolve-puzzle, pero misma familia) | — | Para clúster 17:01:25-37 (12s) ya cubierto por 15 min. |
| Veto cinemático | `30.0 km/h` en `migrate-to-postgres.js:107` y `resolve-puzzle` lo usa en `calculateDistance/timeDelta` | `:107` | A pie en centro Roma 20-30 km/h. Si `speed>30`, exige `histograma >0.95` para heredar. |
| Cache `coordinateResolutionCache` | `Map` con clave `lat.toFixed(4),lng.toFixed(4)` | `:17` | Evita recalcular `Tempio` para mismas coords. |
| `MEMORY.md` | `getLessonsForH3Cells` lee lecciones previas por `h3` | `:37` | Si ya se resolvió `891e...` para Tempio, reutiliza lección. |
| Ventana temporal | `ORDER BY date_taken ASC` + `15 min` | `:77` | Fotos encadenadas del mismo paseo por el Foro Boario. |

**Módulos reutilizables para Tempio sin duplicar:**

- `rankAnchors` tal cual — detectará `Tempio di Portuno` como `LANDMARK` si `visionLabels` trae `tempio`.
- `calculateDistance` + `H3_RESOLUTION=9` + `INHERIT_WINDOW_MS=15 min` — aplicar idéntico.
- `coordinateResolutionCache` y `memoryStore.findMatch(h3Index,...)` (L1) — ya implementados.
- No crear `resolve-tempio.js` nuevo; invocar `resolve-puzzle.js` con lote filtrado por `bbox` Tempio.

---

## 2. Cruce de Verdad de Campo — Datasets Geomática Vision AI `data/landmarks/`

| Archivo | Features | H3 únicos | Anclas | Estructura | Uso para Tempio di Portuno |
|---|---|---|---|---|---|
| `dataset_roma_italia.geojson` | 30 | 25 | 19 | `FeatureCollection` Point ` [lng,lat]` + `properties: {id, coordinates{lat,lng,corner}, timestamp, lighting{sunPosition,shadowDirection}, microPhysiognomy{aerialCables,shutterStyle,treeType,graffiti,terrain,urbanElements{furniture,vegetationScore,architectureStyle}}, ocr{detectedText,confidence,rapidFuzzScore}, exif{fStop,iso,make,model,dateTimeOriginal}, validation{distanceFromCenter,isOutlier,computedScore,issues,h3Index}, h3Index, geocodingScore, isAnchor}` | Cobertura Roma general, incluye `Tempio di Portuno` como punto `Foro Boario` con `h3` cercano a `12.483,41.889`. Radio útil: `validation.distanceFromCenter` hasta 1329m para NW, pero `h3Index` específico para Tempio (`12.4830,41.8895` ~ `891e...`). |
| `dataset_roman_forum_rome.geojson` | 30 | 25 | 19 | Idéntica estructura, `groundedFromAnchor: Trastevere/Colosseum/...` | Mismo punto Tempio pero desde contexto Foro. Permite validar que `Tempio` no está aislado: comparte `locationContext: Roma` y `h3` con `dataset_roma_italia`. |
| `dataset_coliseo_roma.geojson` | 110 | 21 | 82 | Misma estructura, `isAnchor` 82/110, `computedScore 81-126` | No contiene Tempio, pero demuestra patrón: Coliseo usa `h3 891e8052a6bffff` para 82 anclas. Tempio debe agruparse en su propio `h3` distinto, no heredar `a6bffff`. |
| `dataset_*_roma.geojson` (generales) | — | — | — | `grep -i portuno` encuentra `Tempio di Portuno` en 5 datasets: `dataset_bas_lica_de_santa_mar_a_la_may.geojson`, `dataset_fontana_di_trevi...`, `dataset_stazione_termini...` etc., con `coordinates 12.483,41.889` y `h3` estable | Confirma que el motor actual ya indexa Tempio en múltiples colecciones; el radio de cobertura efectivo es `validation.distanceFromCenter` del punto más cercano: para Tempio `~80-120m` si se filtra por `h3` exacto, no por `distanceFromCenter` de 500m genérico. |

**Radio de cobertura para `Tempio di Portuno; Roma; Italia;`:**
- No usar `distanceFromCenter` de 500m del dataset (es outlier 865m para Piazza Navona). Usar `h3Index` del punto `Tempio` (`12.4830,41.8895` -> `h3 ~891e805...` a calcular con `latLngToCell(41.8895,12.4830,9)`).
- En `geojson-cache.js` el `bbox` del `Feature` de Tempio ya es el radio: filtrar `known_places` por `h3_res9 = latLngToCell(41.8895,12.4830,9)` y `ST_DWithin(geom::geography, ..., 170)` (diámetro H3), no 500m. Así evitas traer `Fontana di Trevi` a 570m.

---

## 3. Informe de Arquitectura e Integración Urbana — Tempio di Portuno

### Módulos Reutilizables (no duplicar scripts)

- **`apps/frontend/api/geojson-cache.js:82` `SELECT ... FROM known_places WHERE review_status='RECONSTRUCTED'`** — ya sirve Tempio si `h3_res9` está poblado. Solo asegurar que el `INSERT` de Tempio use `review_status='RECONSTRUCTED'` y `h3_res9 = latLngToCell(41.8895,12.4830,9)`.

- **`apps/frontend/api/resolve-puzzle.js:584` `rankAnchors` + `apps/frontend/api/resolve-puzzle.js:104` `calculateDistance` + `H3_RESOLUTION=9` + `INHERIT_WINDOW_MS=15 min`** — aplicar tal cual. No crear `resolve-tempio.js`.

- **`apps/frontend/api/utils/spatial-utils.js` `loadWorldGeoJson`** — ya cachea países, no tocar.

### Ajuste Cinemático (20-30 km/h, sin APIs externas)

- **Ventana:** `INHERIT_WINDOW_MS = 15 min` (`resolve-puzzle.js:77`). Para Tempio, fotos del mismo paseo por Foro Boario (ej. 11:20 Piazza Navona -> 13:45 Testaccio) **no** heredan porque `>15 min` y `h3` distinto. Solo heredan ráfagas `<=15 min` en misma `h3` `891e805...` (ej. clúster 17:01:25-37 del Túnel ya validado).
- **Veto:** `speed = distance / (timeDelta/60)` con `calculateDistance`. Si `speed >30` y `timeDelta <=60 min` (caso `audit_mayo.py` con 95 km en 0.5 min -> 12306 km/h), exige `histograma >0.95` o no hereda. Para Tempio a pie en Roma, `30 km/h` es estricto y evita que una foto de `Trastevere` herede `Tempio` a 1.3 km en 5 min (15 km/h sí pasa, 30 no).
- **Herencia:** `memoryStore.findMatch(h3Index, lat, lng, heading)` L1 ya implementado. Si `Tempio` ya está en `spatial_cache` con `h3`, `findMatch` lo devuelve sin `Photon`/`Overpass`. Sin `heading`, `calculateHeadingDelta` retorna `true` (no bloquea).
- **Sin APIs:** Todo local: `h3-js`, `calculateDistance`, `coordinateResolutionCache` Map, `MEMORY.md`. `find-poi.js` con `ST_DWithin(geom::geography, ..., 170)` y `vector_cosine` solo si hay `embedding`.

### Estructura de la Tabla (`photo_catalog.db` -> `known_places` / `spatial_cache`)

**Estado actual `photo_catalog.db` (`PRAGMA table_info`):**
- `photos` ya tiene `h3_index`, `place_name`, `tags`, `location_time`, `latitude/longitude` (4 decimales), `location_source`, `confidence_score`, `trip_name`. No necesita `ALTER` para Tempio.
- `spatial_cache` y `known_places` ya existen en PostGIS (migración `001_add_postgis...` con `geom POINT 4326`, `h3_index VARCHAR(15) CHECK ~ '^[0-9a-f]{15}$'`, `embedding vector`, `GIST`/`HNSW`).

**Sugerencia de acople (no duplicar tabla):**
- No crear `tempio_places`. Reutilizar `known_places`:
  ```sql
  INSERT INTO known_places (place_id, name, anon_latitude, anon_longitude, h3_res9, place_data, review_status, confidence_score)
  VALUES ('tempio-portuno-001', 'Tempio di Portuno; Roma; Italia;', 41.8895, 12.4830, latLngToCell(41.8895,12.4830,9), '{"type":"Feature","geometry":{"type":"Point","coordinates":[12.4830,41.8895]}}', 'RECONSTRUCTED', 1.0)
  ON CONFLICT (place_id) DO NOTHING;
  ```
- `photo_catalog.db` `photos` sigue como stage; `known_places` es la caché de verdad para `geojson-cache.js`. `Tempio` no necesita `trip_name` nuevo; usa `tags='{"place_hito":"Tempio di Portuno","evento_viaje":"viaje_italia_2023"}'` y `place_name='Tempio di Portuno; Roma; Italia;'`.

**Pipeline Tempio sin falsos positivos:**
1. `api/geojson-cache.js` sirve `bbox` Roma filtrado.
2. `api/resolve-puzzle.js` con `H3 9 + 15 min + 30 km/h + rankAnchors` asigna `Tempio` solo si `h3` coincide y `distance/time` pasa veto.
3. `photo_catalog.db` persiste `h3_index` y `place_name` con transacción `BEGIN/COMMIT` por lotes 1000, sin tocar `EXIF_GPS` nativo.

---
*Auditoría sin duplicación: reutilizar `geojson-cache.js:40` + `resolve-puzzle.js:77/104/584` y datasets `data/landmarks/dataset_roma_italia.geojson` con `h3` para Tempio.*
