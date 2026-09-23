# Informe Correccion Mapeo Temporal Estricto - 04-Abril 2023

**Algoritmo temporal obligatorio: comparacion `photo.date_taken` (EXIF) contra rangos `start_datetime` a `end_datetime` de vouchers. Prohibido usar `filename`/`file_path`.**

## Vouchers con rangos temporales definidos
- **BIH_2304_BOSNIA**: `BIH 2304 - Tunel Spasa / Sarajevo Tunnel Museum`
  - Rango: `2023-04-28 00:00:00 a 2023-04-30 23:59:59`
  - Lugar verdadero: `Tunel Spasa, Sarajevo, Donji Kotorac, Ilidza, Bosna i Hercegovina`
  - Coordenadas: `43.8246,18.3408` (4 decimales ~11m) h3=`891ef459257ffff`
  - Evento: `viaje_bosnia_2023` fuente: `BIH 2304 pdf + BenGurion 2023-04-29 08:25 + Skenderija 1 + Nominatim Tunel Spasa`
- **ITALIA_2023_ROMA**: `Italia 2023 - Capilla Sixtina / Museos Vaticanos`
  - Rango: `2023-04-01 00:00:00 a 2023-04-27 23:59:59`
  - Lugar verdadero: `Viale Vaticano, 95, 00192 Roma RM, Italia`
  - Coordenadas: `41.9074,12.455` (4 decimales ~11m) h3=`891e805058bffff`
  - Evento: `viaje_italia_2023` fuente: `Capilla Sixtina pdf + Booking_Italia_2023_Hoteles.png`

## Fotos analizadas: 172 con `date_taken` abril 2023
- Actualizadas por rango temporal: **172**
- Reasignadas correctamente (cambio de lugar/coords): **158**

## Fotos reasignadas por rango temporal EXIF (muestra)
| Archivo | date_taken EXIF | Voucher rango | Lugar anterior -> Lugar corregido | Coord corregida | H3 Res9 | evento_viaje | location_time |
|---|---|---|---|---|---|---|---|---|
| VID-20210209-WA0015.mp4 | 2023-04-12 14:55:24 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:12 14:55:24 |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b075b.jpg | 2023-04-22 10:20:35 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:22 10:20:35 |
| 20230401_111652.jpg | 2023-04-01 11:16:53 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:01 11:16:53 |
| 20230401_113233.jpg | 2023-04-01 11:32:33 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:01 11:32:33 |
| 20230401_113236.jpg | 2023-04-01 11:32:36 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:01 11:32:36 |
| 20230401_113313.jpg | 2023-04-01 11:33:14 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:01 11:33:14 |
| 20230401_120553.jpg | 2023-04-01 12:05:53 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:01 12:05:53 |
| 20230428_100755.jpg | 2023-04-28 10:07:55 | BIH_2304_BOSNIA | NULL -> Tunel Spasa, Sarajevo, Do | 43.8246,18.3408 | 891ef459257ffff | viaje_bosnia_2023 | 2023:04:28 10:07:55 |
| 20230428_100909.jpg | 2023-04-28 10:09:09 | BIH_2304_BOSNIA | NULL -> Tunel Spasa, Sarajevo, Do | 43.8246,18.3408 | 891ef459257ffff | viaje_bosnia_2023 | 2023:04:28 10:09:09 |
| 20230428_101000.jpg | 2023-04-28 10:10:00 | BIH_2304_BOSNIA | NULL -> Tunel Spasa, Sarajevo, Do | 43.8246,18.3408 | 891ef459257ffff | viaje_bosnia_2023 | 2023:04:28 10:10:00 |
| 20230429_051452.jpg | 2023-04-29 05:14:52 | BIH_2304_BOSNIA | NULL -> Tunel Spasa, Sarajevo, Do | 43.8246,18.3408 | 891ef459257ffff | viaje_bosnia_2023 | 2023:04:29 05:14:52 |
| IMG-20230401-WA0007.jpg | 2023-04-01 18:15:24 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:01 18:15:24 |
| IMG-20230402-WA0002.jpeg | 2023-04-02 13:25:45 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:02 13:25:45 |
| IMG-20230403-WA0012.jpeg | 2023-04-03 11:26:18 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:03 11:26:18 |
| IMG-20230404-WA0002.jpeg | 2023-04-04 09:01:43 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:04 09:01:43 |
| IMG-20230405-WA0006.jpg | 2023-04-05 12:45:08 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:05 12:45:08 |
| IMG-20230406-WA0000.jpg | 2023-04-06 10:30:46 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:06 10:30:46 |
| IMG-20230407-WA0000.jpg | 2023-04-07 06:37:28 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:07 06:37:28 |
| IMG-20230408-WA0001.jpg | 2023-04-08 15:57:25 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:08 15:57:25 |
| IMG-20230409-WA0001.jpeg | 2023-04-09 10:02:50 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:09 10:02:50 |
| IMG-20230410-WA0000.jpg | 2023-04-10 06:02:52 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:10 06:02:52 |
| IMG-20230411-WA0003.jpg | 2023-04-11 09:12:18 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:11 09:12:18 |
| IMG-20230413-WA0003.jpg | 2023-04-13 07:20:23 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:13 07:20:23 |
| IMG-20230414-WA0000.jpg | 2023-04-14 04:12:53 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:14 04:12:53 |
| IMG-20230415-WA0000.jpg | 2023-04-15 19:12:27 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:15 19:12:27 |
| IMG-20230416-WA0004.jpeg | 2023-04-16 14:06:06 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:16 14:06:06 |
| IMG-20230417-WA0006.jpeg | 2023-04-17 09:58:06 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:17 09:58:06 |
| IMG-20230418-WA0003.jpeg | 2023-04-18 11:28:55 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:18 11:28:55 |
| IMG-20230419-WA0000.jpeg | 2023-04-19 08:04:22 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:19 08:04:22 |
| IMG-20230420-WA0002.jpg | 2023-04-20 05:57:12 | ITALIA_2023_ROMA | NULL -> Viale Vaticano, 95, 00192 | 41.9074,12.455 | 891e805058bffff | viaje_italia_2023 | 2023:04:20 05:57:12 |
| ... (128 mas) | ... | ... | ... | ... | ... | ... | ... |

## Ejemplo destacado (error previo corregido)
- **Foto `2023-04-29 17.08.59_Italia_2023.jpg`** con `date_taken=2023-04-29 17:08:59` cae dentro de `BIH_2304_BOSNIA` (`2023-04-28 a 2023-04-30`).
  - **Antes (error por nombre)**: asignada a `Viale Vaticano, Roma` (41.9074,12.455) por contener 'Italia' en filename.
  - **Ahora (temporal correcto)**: `Tunel Spasa, Sarajevo` = `43.8246,18.3408` h3=`891ef459257ffff` `evento_viaje=viaje_bosnia_2023` **incondicionalmente** por rango voucher.
- Todas las fotos `2023-04-29` y `2023-04-30` con `*_Italia_2023.jpg` fueron reasignadas a Bosnia por temporal, demostrando correccion estricta.

## Persistencia
- `BEGIN TRANSACTION/COMMIT` en `data/photo_catalog.db`: 172 registros con `latitude`/`longitude`/`lat`/`lng` (4 decimales), `h3_index` Res9, `place_name`, `tags` JSON 3D
- `location_time` = `date_taken` EXIF verificado, sin desfasaje adicional
- Velocity Veto no aplica aqui (rango voucher manda), pero H3 coherente con lugar real

## Validacion
- Ninguna asignacion uso `filename`/`file_path` para decidir ubicacion (verificado por codigo)
- Tags `evento_viaje` corregido a `viaje_bosnia_2023` para fechas Bosnia, `viaje_italia_2023` para resto abril