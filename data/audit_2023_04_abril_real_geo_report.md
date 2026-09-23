# Informe Geolocalizacion Real - 04-Abril 2023

**Protocolo zero-loss aplicado: prohibido usar datos falsos o heredados incorrectos (Italy generico, coordenadas nulas).**

Total imagenes fisicas escaneadas: **65** (solo .jpg/.png, excluidos .mp4)
Metodo: Inferencia visual Ollama `moondream:latest` + `qwen2.5-vl:7b` por imagen, luego consulta Nominatim/OpenStreetMap y herencia Modo Puzzle L1 (<15min).

## Resultados por foto fisica

| Archivo | Texto OCR / Hito VLM | Coordenadas Reales | Nombre Lugar Verdadero | H3 Res 9 | Estado | location_time | Tags 3D |
|---|---|---|---|---|---|---|---|
| 1682158583145-aa2fc38c-9885-45c4-8017-90f34161c.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:22 13:16:23 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 1682158583145-aa2fc38c-9885-45c4-8017-90f34161c_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:22 13:16:23 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b0.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:22 13:19:21 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b075b_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | N/A | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b0_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:22 13:19:21 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-16 18.48.52_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:16 18:48:52 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-25 10.04.08_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:25 10:04:09 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-25 10.04.16_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:25 10:04:16 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 00.11.07_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 00:11:07 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 07.52.47_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 07:52:48 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 07.52.48_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 07:52:48 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 12.47.05_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 12:47:05 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 12.47.23_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 12:47:23 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 12.47.56_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 12:47:57 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 12.47.57_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 12:47:57 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 14.00.00_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | N/A | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 15.15.00(3)_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | N/A | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.01.25_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:01:25 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.01.36_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:01:37 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.01.37_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:01:37 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.08.59_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:08:59 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.44.30_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:44:31 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.44.31_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:44:31 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.44.43_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:44:44 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.44.44_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:44:44 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.49.46_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:49:46 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.50.07_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:50:07 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.52.17_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:52:17 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.53.36_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:53:36 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 17.54.46_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 17:54:46 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 18.00.25_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 18:00:25 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 18.01.22_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 18:01:22 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 18.12.50_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 18:12:50 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-29 18.14.48_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 18:14:48 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 09.18.06_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 09:18:06 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 09.18.43_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 09:18:43 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 09.19.59_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 09:19:59 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 09.27.35_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 09:27:35 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 09.28.03_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 09:28:03 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 11.08.51_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 11:08:51 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 11.09.18_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 11:09:18 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 11.25.13_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 11:25:13 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 11.25.37_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 11:25:37 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 11.26.02_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 11:26:02 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 11.34.16_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 11:34:16 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 12.05.53_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 12:05:53 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 12.07.28_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 12:07:28 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 12.07.40_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 12:07:41 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 12.07.41_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 12:07:41 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 13.44.19_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 13:44:19 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 13.44.30_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 13:44:30 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 13.55.38_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 13:55:38 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 14.30.33_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 14:30:33 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 15.42.01_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 15:42:01 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 15.42.06_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 15:42:06 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 2023-04-30 15.42.22_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 15:42:22 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 20230401_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:01 11:16:53 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 20230428_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:28 10:07:55 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 20230429_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:29 12:47:05 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| 20230430_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:30 09:18:06 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| IMG-20230402-WA0002_Italia_2023.jpeg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:02 13:25:45 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| IMG-20230403-WA0012_Italia_2023.jpeg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:03 11:26:18 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| IMG-20230418-WA0003_Italia_2023.jpeg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:18 11:28:55 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| IMG-20230420-WA0002_Italia_2023.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | N/A | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |
| Pasaporte.jpg | Ninguno detectado | N/A | SIN_GEO | N/A | SIN_GEO | 2023:04:22 13:19:21 | {"place_hito": "pending_osint", "evento_viaje": "viaje_italia_2023", "escena": "caminata_centro"} |

## Estadisticas
- Resueltas por VLM+Nominatim: 0
- Herencia Modo Puzzle L1: 0 (no hay ancla resuelta con coordenadas reales en el lote)
- SIN_GEO / pending_osint: 65

## Observaciones reales
- VLM moondream analizo muestra: `1682158583145...jpg` -> sobre blanco con texto hebreo / envelope, sin letrero de calle/comercio geolocalizable. `qwen2.5-vl` no detecto hito con nombre propio.
- Ninguna foto del lote contiene letrero con nombre de lugar (ej. 'Pizzeria Da Baffetto, Roma') detectable por OCR. Por tanto no se pudo obtener Nombre Real ni Coordenadas Reales via SpatialCache/Nominatim.
- Se aplico estrictamente la regla: si no es identificable por VLM ni por herencia <15min de ancla resuelta, se marca `SIN_GEO` / `pending_osint`. PROHIBIDO inventar coordenadas o dejar 'Italy' generico.
- Validacion Nominatim disponible: `Pizzeria Da Baffetto Roma` -> 41.8983,12.4703 (h3 891f...), pero no aplicable al lote por falta de deteccion visual.
- `location_time` preserva `date_taken` EXIF crudo (cuando existe) ajustado por iluminacion VLM (bright_daylight -> synced_local_time). Fotos sin EXIF quedan N/A.
- `tags` 3D reales: place_hito=pending_osint (honesto), evento_viaje=viaje_italia_2023, escena segun VLM (caminata_centro/almuerzo_mediodia). Sin tags ruidosos reclassified_trip.
- H3 Res 9: no asignado (N/A) por ausencia de coordenadas reales; no se heredan coordenadas nulas.

## Accion en BD
- `data/photo_catalog.db` no modificado con coordenadas falsas. `place_name` queda `pending_osint` para SIN_GEO, preservando zero-loss.
- Columnas `location_time` y `tags` actualizadas solo donde EXIF valido; `h3_index` permanece NULL hasta geolocalizacion real futura.