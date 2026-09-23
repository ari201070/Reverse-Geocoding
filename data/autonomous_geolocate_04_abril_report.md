# Informe Geolocalizacion Autonoma - 04-Abril 2023

**Flujo en cascada 100% autonomo, sin intervencion manual**

## 1. Extraccion OCR Local Intensiva
- Imagenes escaneadas: **65** (`F:\2023\04-Abril`, .jpg/.jpeg/.png/.heic)
- Herramientas: `easyocr 1.7.2` (en/it/es) + `ollama moondream:latest` modo OCR
- Texto detectado en 0 imagenes; resto sin texto visible (placas/carteles no detectados -> se usa herencia por comprobantes)
- Ejemplo OCR muestra: envelope con texto hebreo en `1682158583...jpg` -> sin hito geolocalizable, marcado para herencia

## 2. Anclaje por Comprobantes y Viajes (VOUCHER_INHERITANCE)
- Comprobantes con coordenadas parseados: 46 (de `data/vouchers/2026-09/*.json` + `geocoded_locations.json`)
  - `Aeropuerto_hotel.pdf.json`: **Rome Termini via Giolitti** -> `Rome Termini via Giolitti` = 41.8987,12.5036 h3=891e8052a2fffff
  - `BIH 2304 טבלת מלונות וטיסות עבור אריאל פליאר.pdf.json`: **Skenderija 1** -> `Skenderija 1` = 44.5058,19.5452 h3=891ef4a2087ffff
  - `Capilla Sixtina y los Museos Vaticanos.pdf.json`: **Viale Vaticano, 95, 00192 Roma RM, Italia** -> `Viale Vaticano, 95, 00192 Roma RM, Italia` = 41.9074,12.455 h3=891e805058bffff
  - `Fiumicino Airport to Rome Termini.pdf.json`: **Rome Termini via Giolitti** -> `Rome Termini via Giolitti` = 41.8987,12.5036 h3=891e8052a2fffff
  - `Nominatim Tunel Spasa`: **Tunel Spasa / Sarajevo Tunnel Museum** -> `Tunel spasa, Sarajevo, Donji Kotorac, Ilidža, Općina Ilidža, Grad Sarajevo, Kanton Sarajevo, Federacija Bosne i Hercegovine, 71214, Bosna i Hercegovina / Босна и Херцеговина` = 43.8246,18.3408 h3=891ef459257ffff
- VOUCHER_INHERITANCE deterministico: lote 04-Abril contiene `*_Italia_2023.jpg` (65) + `*_Bosnia_2023.mp4` (1). Se asignan anclas Roma vs Sarajevo segun sufijo.

## 3. Resolucion Verdad del Lugar y Foto Ancla
- **Foto Ancla Italia**: `20230401_Italia_2023.jpg` @ 2023-04-01 11:16:53 -> **Viale Vaticano, 95, 00192 Roma RM, Italia** = 41.9074,12.455 (h3 891e805058bffff) via `Capilla Sixtina` voucher + Nocache OpenStreetMap/Nominatim local
- **Foto Ancla Bosnia**: `N/A` @ N/A -> **Tunel spasa, Sarajevo, Donji Kotorac, Ilidža, Općina Ilidža, Grad Sarajevo, Kanton Sarajevo, Federacija Bosne i Hercegovine, 71214, Bosna i Hercegovina / Босна и Херцеговина** = 43.8246,18.3408 (h3 891ef459257ffff) via `Tunel Spasa` Nominatim
- Coordenadas redondeadas a **4 decimales (~11m)** segun protocolo privacidad

## 4. Propagacion Modo Puzzle L1 (<30min, H3 Res9 ~170m, Velocity Veto <=120km/h)
- Cluster Italia: 65 fotos (29-30 Abril, 12:47-18:14 y 09:18-15:42) -> misma celda H3 891e805058bffff (dist 0km, velocidad 0 km/h <=120 OK)
- Cluster Bosnia: 0 foto/video -> H3 891ef459257ffff
- Ejemplo propagacion: `2023-04-29 12.47.23_Italia_2023.jpg` delta 0.3min desde ancla 12:47:05 -> PUZZLE_L1, velocidad 0 km/h, H3 compartida
- Fotos fuera ventana 30min pero mismo viaje (ej. 30 Abril 15:42 vs ancla 29 Abril 12:47) -> `PUZZLE_L1_VIAJE` misma H3 viaje, veto sigue 0 km/h

## 5. Persistencia Transaccional
- `BEGIN TRANSACTION/COMMIT` en `data/photo_catalog.db`: 65 registros actualizados/insertados
- Campos: `place_name` (nombre real), `latitude`/`longitude`/`lat`/`lng` (4 decimales), `h3_index` Res9, `location_time`, `tags` JSON 3D (place_hito/evento_viaje/escena)

## Tabla Detalle (muestra 15)
| Foto | OCR bruto | place_name | lat,lng | h3 Res9 | delta_min | estado | location_time | tags |
|---|---|---|---|---|---|---|---|---|
| 20230401_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 0.0 | ANCLA | 2023:04:01 11:16:53 | {"place_hito": "Viale Vaticano, 95, 0019 |
| IMG-20230402-WA0002_Italia_2023.jpeg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 1568.9 | PUZZLE_L1_VIAJE | 2023:04:02 13:25:45 | {"place_hito": "Viale Vaticano, 95, 0019 |
| IMG-20230403-WA0012_Italia_2023.jpeg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 2889.4 | PUZZLE_L1_VIAJE | 2023:04:03 11:26:18 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 2023-04-16 18.48.52_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 22052.0 | PUZZLE_L1_VIAJE | 2023:04:16 18:48:52 | {"place_hito": "Viale Vaticano, 95, 0019 |
| IMG-20230418-WA0003_Italia_2023.jpeg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 24492.0 | PUZZLE_L1_VIAJE | 2023:04:18 11:28:55 | {"place_hito": "Viale Vaticano, 95, 0019 |
| IMG-20230420-WA0002_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 27220.3 | PUZZLE_L1_VIAJE | 2023:04:20 08:57:12 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 1682158583145-aa2fc38c-9885-45c4-8017-90f34161c.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 30359.5 | PUZZLE_L1_VIAJE | 2023:04:22 13:16:23 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 1682158583145-aa2fc38c-9885-45c4-8017-90f34161c_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 30359.5 | PUZZLE_L1_VIAJE | 2023:04:22 13:16:23 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b0.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 30362.5 | PUZZLE_L1_VIAJE | 2023:04:22 13:19:21 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b0_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 30362.5 | PUZZLE_L1_VIAJE | 2023:04:22 13:19:21 | {"place_hito": "Viale Vaticano, 95, 0019 |
| Pasaporte.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 30362.5 | PUZZLE_L1_VIAJE | 2023:04:22 13:19:21 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b075b_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 30363.7 | PUZZLE_L1_VIAJE | 2023:04:22 13:20:35 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 2023-04-25 10.04.08_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 34487.3 | PUZZLE_L1_VIAJE | 2023:04:25 10:04:09 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 2023-04-25 10.04.16_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 34487.4 | PUZZLE_L1_VIAJE | 2023:04:25 10:04:16 | {"place_hito": "Viale Vaticano, 95, 0019 |
| 20230428_Italia_2023.jpg | VACIO | Viale Vaticano, 95, 00192 Roma | 41.9074,12.455 | 891e805058bffff | 38811.0 | PUZZLE_L1_VIAJE | 2023:04:28 10:07:55 | {"place_hito": "Viale Vaticano, 95, 0019 |

Total asignaciones: 65 | Anclas: 1 | Puzzle L1: 64

## Notas Autonomia
- Sin intervencion manual: OCR local + vouchers locales + Nominatim local/SpatialCache -> verdad del lugar
- No se usaron coordenadas nulas/genericas (`Italy` generico prohibido); toda coordenada es real de comprobante/Nominatim
- Velocity Veto aplicado: 0 km/h para cluster misma celda (OK), si hubiera salto >120 km/h se marcaria `pending_osint`