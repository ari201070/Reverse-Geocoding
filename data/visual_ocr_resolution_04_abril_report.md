# Informe Resolucion Visual OCR + POI - 04-Abril 2023

**Fotos pending escaneadas:** 64 en `F:\2023\04-Abril`
**OCR local:** `easyocr`/`qwen2.5-vl:7b` (Ollama) para carteles/placas + descripcion POI
**Geocodificacion:** `SpatialCache` + `Nominatim` local

**Fotos Ancla por cartel/POI:** 0
**Fotos propagadas Modo Puzzle <15min:** 0
**Total resueltas:** 0
**DB actualizados:** 0 | **EXIF actualizados:** 0

## Carteles / POIs detectados y coordenadas asignadas
| Foto Ancla | OCR Cartel | POI Desc | Coordenadas | place_name | H3 Res9 | Query |
|---|---|---|---|---|---|---|
| *ninguna* | VACIO | VACIO | NULL | pending_osint | NULL | - |

> **Ningun cartel/POI geolocalizable detectado en las 64 fotos pending.** Ejemplo OCR `1682158583...jpg` -> envelope hebreo sin direccion, `2023-04-29 12.47...jpg` -> fachada sin letrero legible. Validado con `qwen2.5-vl:7b` y `easyocr` sin texto de calle/comercio.

## Fotos propagadas por Modo Puzzle (<15 min)
| Foto Propagada | dt | Heredado de Ancla | Coordenadas | place_name | H3 | Delta |
|---|---|---|---|---|---|---|
| *ninguna* | - | - | - | - | - | - |

## Pendientes restantes
- Fotos que permanecen `pending_osint` (sin cartel/POI y sin ancla <15min): **64**
- Se mantiene `place_name=pending_osint`, `latitude=NULL`, `h3_index=NULL` (cero coordenadas inventadas)

## Validacion
- Prohibicion cumplida: ninguna foto `pending_osint` con cartel/POI reconocible quedo sin resolver
- Si no hay cartel/POI geolocalizable, se mantiene pendiente honestamente
- Actualizacion DB y EXIF fisico solo para fotos resueltas, dentro de `BEGIN TRANSACTION/COMMIT`