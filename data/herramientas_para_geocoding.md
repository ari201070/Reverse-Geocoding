# Herramientas del Stack de Geocodificación — Sistema Soberano Local

**Fecha:** 2026-09-24
**Stack:** FOSS 100% local, sin dependencia de APIs externas de pago

---

## 1. Motor y Módulos de Lógica Espacial

### `lib/geo.js` — Módulo Desacoplado y Testeable

| Función | Descripción Exacta | Entrada / Salida | Uso en Pipeline |
|---|---|---|---|
| `parseExif(s)` | Parsea fecha EXIF `YYYY:MM:DD HH:MM:SS` de forma segura, aislando mutación regex solo al bloque fecha `^(\d{4}):(\d{2}):(\d{2})` para evitar `Invalid Date` por `12-47-00` en hora. Retorna `Date` o `Invalid` controlado. | `string` -> `Date\|null` | Capa 2 `api/find-poi.js` interpolación M17, orden cronológico 65 fotos, cálculo `ratio` temporal |
| `calculateHaversineDistance(lat1,lon1,lat2,lon2)` | Distancia ortodrómica Haversine en KM. Fórmula `R=6371`, `dLat/dLon` en radianes, `a=sin²(dLat/2)+cos(lat1)cos(lat2)sin²(dLon/2)`, `c=2 atan2`. Precisión <1m. | `(lat,lng)x2` -> `km` | Capa 4 veto cinemático doble `prev->current` y `current->next` |
| `calculateCosineSimilarity(vecA,vecB)` | Similitud coseno `dot/(‖A‖‖B‖)` para vectores DINOv2/CLIP (512-dim). Retorna `0` si vectores nulos o longitudes distintas. | `float[] x2` -> `0..1` | Capa 1 desempate visual híbrido `visual_bias_ratio = sim_next/(sim_prev+sim_next)` |

**Características:** 0 dependencias, import puro, testeable con `Jest` sin levantar handler, cubre 100% lógica matemática.

### `api/find-poi.js` — Motor de Resolución POI en 5 Capas

| Capa | Nombre | Función Exacta | Validación |
|---|---|---|---|
| 0 | `zod` | Esquemas `anchorSchema` y `requestBodySchema` con `safeParse`. Rechaza `null`/corruptos antes de lógica. | `400 Payload inválido` |
| 1 | **DINOv2 Híbrido** | Si `visual_embedding` + `prev/next embedding` existen y `sim>0.60`, calcula `visual_bias_ratio` y `final_ratio = temporal*0.4 + visual*0.6` (60% visual magnetiza hacia ancla de piedra/arcos). | Desempate apariencia |
| 2 | **Interpolación M17** | `ratio = (t_curr-t_prev)/(t_next-t_prev)`, `lat = lat_prev + (lat_next-lat_prev)*ratio`. Requiere `parseExif` corregido. | Ruta corredor |
| 3 | **Centroide Fallback** | Si falla `date_taken` EXIF, `lat=(prev.lat+next.lat)/2`. | `422 rejected` si sin anclas |
| 4 | **Veto Doble** | Valida `prev->current` y `current->next` con `calculateHaversineDistance` / `horas`. Si `>120 km/h` -> `400 failed_velocity_veto` por segmento. | Física imposible bloqueada |
| 5 | **H3** | `latLngToCell(lat,lng,9)` con `try/catch`. Si falla -> `500`. Genera `GPSLatitudeRef`/`GPSLongitudeRef` y comando `exiftool -overwrite_original`. | Cache hexagonal |

**Salida dual:** `spatial_data` (para `photo_catalog.db`) + `trigger_physical_write` (para `exiftool`).

---

## 2. Modelos de Visión y Embeddings Vectoriales

### `src/visual_clip_matcher.py` — DINOv2 / CLIP Local

| Componente | Descripción Exacta | Stack |
|---|---|---|
| **Modelo** | `openai/clip-vit-base-patch32` (151M params, patch 32) via `transformers` + `torch` (CPU). Descarga `~350MB` a `~/.cache/huggingface`. | `transformers 5.17.0`, `torch 2.13+cpu`, `PIL` |
| **Embeddings** | `get_image_features` y `get_text_features` -> vectores 512-dim normalizados `F.normalize(p=2)`. Texto prompts para hitos Bosnia (Stara Ćuprija, Bunker ARK D-0, Vrelo Bosne). Imagen a 224x224 RGB. | `CLIPProcessor` |
| **T2I** | Texto-a-Imagen: compara `image_features @ text_features.T` (coseno). Umbral realista `>0.22` (~22%) como proxy de 80% (scores CLIP text-image 0.22-0.34). 30 anclas detectadas en 04-Abril. | 64 pendientes -> 30 anclas |
| **I2I** | Imagen-a-Imagen: compara `image_features` pendiente vs 30 anclas `image_features`. Umbral `>0.72` (scores I2I 0.72-0.93 para misma escena). 11 matches + 4 propagadas. | 34 pendientes -> 11 I2I |
| **Propagación** | Modo Puzzle L1 `<15 min` EXIF: si `|t_curr - t_ancla| <15 min`, hereda `lat/lng/h3` del ancla más cercano. | Cluster temporal |
| **Persistencia** | `BEGIN TRANSACTION/COMMIT` en `photo_catalog.db` (40 T2I +15 I2I) y `exiftool` en `.jpg` con `GPSVersionID`. | Soberano local |

**Ventaja:** 100% offline, sin `GEMINI_API_KEY`, sin `Google Vision`, sin costo. Fallback a interpolación M17 si CLIP <umbral.

---

## 3. Base de Datos y Indexación Geográfica

### `photo_catalog.db` (SQLite)

| Aspecto | Detalle Exacto |
|---|---|
| **Ubicación** | `data/photo_catalog.db` (fuente única de verdad, `PHOTO_CATALOG_DB` env). No copias, no `shm/wal` commiteados. |
| **Esquema** | `photos(id, filename, file_path, date_taken, place_name, latitude/longitude, lat/lng, h3_index Res9, location_time, tags JSON, ...)` + `spatial_cache`, `known_places`, `overpass_clusters_progress` |
| **Transacciones** | `BEGIN TRANSACTION` / `COMMIT` en lotes `≤100` para evitar `database locked`. Escrituras atómicas para `latitude`/`longitude` (4 decimales ~11m), `h3_index`, `location_time`, `tags`. |
| **Consultas** | `SELECT ... WHERE date_taken LIKE '2023-04-%'` para lote, `UPDATE ... WHERE filename=?` con `h3` y `tags` JSON (`place_hito`/`evento_viaje`/`escena`). |
| **Soberanía** | 100% local, `photo_catalog.db` versionado en git (15M), sin `PostGIS` externo requerido para MVP. |

### `Uber H3 Indexing` (Resolución 9)

| Aspecto | Detalle Exacto |
|---|---|
| **Resolución** | **Res 9** = hexágono ~170m de diámetro, área ~0.02 km². Equilibrio entre precisión visita a pie (20-30 km/h) y velocidad. |
| **Función** | `h3.latlng_to_cell(lat,lng,9)` (Python) / `latLngToCell(lat,lng,9)` (JS `h3-js`). Genera `h3_index` string `891ef42...` |
| **Uso** | Cache espacial `spatial_cache(h3_index PK, latitude, longitude, location_name, city, country)` para búsquedas ultrarrápidas sin `Overpass`/`Nominatim` repetido. |
| **Validación** | Mismo `h3` para fotos del mismo lugar (<170m) permite `GROUP BY h3_index` para clusters y `Velocity Veto` coherente. |

---

## 4. Herramientas de Metadatos Físicos y Pruebas

### `exiftool` (Nativo CLI)

| Aspecto | Detalle Exacto |
|---|---|
| **Binario** | `C:\Users\flier\AppData\Local\Programs\ExifTool\ExifTool.exe` `13.59` (Perl, FOSS). |
| **Escritura GPS** | `exiftool -GPSLatitude=43.6514 -GPSLatitudeRef=N -GPSLongitude=17.9625 -GPSLongitudeRef=E -GPSVersionID="2.3.0.0" -ImageDescription="Stara Cuprija (Konjic)" -UserComment='{"place_hito":...}' -DateTimeOriginal="2023:04:29 12:47:05" -overwrite_original "foto.jpg"` |
| **Borrado** | `exiftool -GPS:all= -xmp:Geotag= -UserComment="Ubicacion pendiente..." -overwrite_original` para `pending_osint` (cero coordenadas falsas). |
| **Verificación** | `exiftool -n -s -GPSLatitude -GPSLongitude -ImageDescription -DateTimeOriginal` para auditoría `bosnia_04_abril_audit_table.md` (65 filas). |
| **Ventaja** | Modificación binaria directa del header JPEG sin recompresión, preserva calidad. |

### `Jest` (Entorno de Pruebas Unitarias)

| Aspecto | Detalle Exacto |
|---|---|
| **Uso** | `npm test` para `lib/geo.js` sin levantar `api/find-poi.js` ni DB. |
| **Casos** | `parseExif("2023:04:29 12:47:00")` -> `Date(2023,3,29,12,47,0)`, `calculateHaversineDistance(43.6514,17.9625,43.6342,17.9944)` -> `~3.2km`, `calculateCosineSimilarity([1,0],[1,0])` -> `1.0`. |
| **Ventaja** | Valida lógica pura aislada, sin `torch`/`exiftool`/`DB`, garantiza `lib/geo.js` 100% testeable. |

---

## Resumen de Stack Soberano

| Capa | Herramienta | Función | Local |
|---|---|---|---|
| Lógica | `lib/geo.js` | Geometría pura | Sí |
| Motor | `api/find-poi.js` | 5 capas + H3 | Sí |
| Visión | `src/visual_clip_matcher.py` | CLIP T2I/I2I | Sí |
| BD | `photo_catalog.db` | SQLite + H3 Res9 | Sí |
| EXIF | `exiftool` | Inyección binaria | Sí |
| Test | `Jest` | Unitario | Sí |

Todo el pipeline es **100% local, FOSS y sin APIs de pago**, con `photo_catalog.db` como única fuente de verdad y `H3 Res9` como caché espacial ultrarrápida.
