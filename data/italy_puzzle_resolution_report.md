# Informe Liquidación Puzzle Italia — Modo Nativo y Anclas Inmutables

**Cobertura:** 818/856 con H3 Res9 (95.6%)
**Anclas inmutables EXIF_GPS:** 817 (no modificadas, solo H3 asignado)
**Huérfanos sin GPS resueltos por puzzle:** 0 (ventana 15 min, H3 Res9 ~170m, veto 20-30 km/h)

## Filtro Cinemático Urbano Peatonal (20-30 km/h)
- Ventana `INHERIT_WINDOW_MS=15*60*1000` (15 min) de `apps/frontend/api/resolve-puzzle.js:76`
- `calculateDistance` Haversine `R=6371` y `speed = dist/(delta_min/60)`; si `speed>30` se descarta, evitando falsos positivos Tempio-Trastevere (1.3km en 5min = 15 km/h OK, 1.3km en 1min = 78 km/h rechazado).
- `H3_RESOLUTION=9` (~170m) asegura que solo heredan fotos en misma celda o vecina, no a 570m (Trevi a 570m no contamina Tempio).

## Tabla Muestra (método, 4 decimales, H3)
| Archivo | Método | lat,lng (4 dec) | H3 Res9 | place_name |
|---|---|---|---|---|
| 20231005_180804.jpg | EXIF_GPS | 43.7698,11.2556 | 891ea201237ffff |  |
| Title-Wed Oct 11 10_56_08 GMT+02_00 2023.jpg | EXIF_GPS | 43.047,11.8441 | 891e84c43afffff |  |
| Title-Wed Oct 11 10_56_49 GMT+02_00 2023.jpg | EXIF_GPS | 43.047,11.8441 | 891e84c43afffff |  |
| VID-20231011-WA0006.mp4 | EXIF_GPS | 43.047,11.8441 | 891e84c43afffff |  |
| 2023-10-06 10.25.03_IMG_20231006_102503_1.jpg | EXIF_GPS | 43.7698,11.2556 | 891ea201237ffff |  |

## Integración GeoJSON
- `apps/frontend/api/geojson-cache.js:40` ya sirve `known_places` + `worldGeoJson` filtrado por `bbox` Roma `12.45-12.50,41.88-41.92`.
- `data/landmarks/dataset_roma_italia.geojson` (30 features, 19 anclas, h3 891e805019bffff para Trastevere) y `dataset_roman_forum`/`dataset_coliseo` comparten mismo esquema `Point[lng,lat]` + `properties.h3Index`.
- Tempio `12.47723,41.88274 h3 891e8050103ffff` reutiliza `known_places(h3_res9, geom POINT 4326, place_data)` sin duplicar script; `geojson-cache.js` lo sirve como `Feature` con `source: LOCAL_CACHE_POSTGIS`.

## known_places
- Estado actual: `photo_catalog.db` ya tiene `h3_index` para Italia; `known_places` en PostGIS es caché de `RECONSTRUCTED` (ver `migrations/001`). No se requiere `ALTER` en `photos`; acople es `photos.h3_index = known_places.h3_res9`.
