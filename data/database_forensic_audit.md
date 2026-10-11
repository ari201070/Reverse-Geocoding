# Auditoría forense de bases de datos (solo lectura, sin alteraciones)

Fecha: 2026-10-11. Método: `os.stat` + `sqlite3` URI `mode=ro`.

## Tabla comparativa (datos reales)

| Ruta | Bytes | mtime (epoch) | Tablas | Filas photos | h3_index | place_name | tags | Muestra 2023-04 |
|---|---|---|---|---|---|---|---|---|
| `C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db` | 20725760 | 1791711409 | photos, sqlite_sequence, overpass_clusters_progress, spatial_cache, known_places, api_rate_limits | 32422 | sí (30 cols) | sí | sí | `VID-20210209-WA0015.mp4`, h3 NULL, place `pending_osint` |
| `C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db` | 37560320 | 1784886376 | photos, sqlite_sequence, overpass_clusters_progress | 34992 | no (19 cols) | no | no | N/A (sin columna h3_index) |
| `C:/Users/flier/.gemini/antigravity/scratch/Reverse-Geocoding/photo_catalog.db` | 18378752 | 1789808354 | known_places, sqlite_sequence, photos | 75994 | no (10 cols) | no | no | N/A (sin columna h3_index) |
| `C:/Users/flier/GitHub/Travel-Booking-Document-Hub/document_anchors.db` | 28672 | 1788773911 | document_anchors | N/A (sin tabla photos) | no | no | no | N/A |

## Rutas verificadas inexistentes

- `C:/Users/flier/GitHub/Reverse-Geocoding/photo_catalog.db` (raíz): no existe.
- `F:/photo_catalog.db` (raíz F): no existe.
- `F:/2023`, `F:/2024`, `F:/2025`, `F:/2026` (profundidad 2): sin `.db`.
- `data/*.db` en el repo: solo `data/photo_catalog.db`.

## Lecturas sin interpretación

- Solo la base del repo tiene las columnas del Quality Gate y las tablas `spatial_cache`/`known_places`/`api_rate_limits`.
- Las dos copias de scratch tienen más filas pero esquema viejo (19 y 10 columnas, sin enriquecidas).
- `document_anchors.db` es otra base (anclas de documentos), no catálogo de fotos.
