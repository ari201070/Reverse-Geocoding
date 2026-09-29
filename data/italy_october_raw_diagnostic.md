# Informe Diagnóstico Crudo - Lote Italia Octubre 2023 (F:\2023\10-Octubre)

**Fecha auditoría:** 2026-09-29 19:01:52

**Conteo físico:** 1294 archivos totales en disco
- JPG/JPEG: **1257**
- Video (mp4/mov): **32**
- Otros (pdf/pbm/png/psd/txt): **5**

## Extracción EXIF (exiftool -j -n -s)
- Con `DateTimeOriginal`/`CreateDate` válida: **958/1257** (76.2%)
- Con `GPSLatitude`/`GPSLongitude` nativo: **58/1257** (4.6%)
- **Supervivientes GPS:** 58 fotos con GPS nativo (posibles anclas).
- Sin fecha: **299**

## Compulsa contra photo_catalog.db (periodo 2023-10)
- Registros DB `2023-10`: **905**
- Con GPS en DB: **884**
- Con `place_name` pendiente/NULL: **905**
- Diferencia físico vs DB: físico **1257 JPG** vs DB **905** -> Físico contiene más no catalogado

## Tabla Resumen (primeras 10 fotos físicas)
| Archivo | Fecha EXIF | GPS detectado | Estado en DB |
|---|---|---|---|
| 2023-10-02 09.00.58.jpg | 2023:10:02 09:00:59 | NULL | GPS sin place |
| 2023-10-02 11.28.01.jpg | 2023:10:02 11:28:02 | NULL | GPS sin place |
| 2023-10-02 14.54.11.jpg | 2023:10:02 14:54:12 | NULL | GPS sin place |
| 2023-10-02 14.54.16.jpg | 2023:10:02 14:54:16 | NULL | GPS sin place |
| 2023-10-02 14.54.20.jpg | 2023:10:02 14:54:21 | NULL | GPS sin place |
| 2023-10-02 14.54.25.jpg | 2023:10:02 14:54:25 | NULL | GPS sin place |
| 2023-10-02 14.55.07.jpg | 2023:10:02 14:55:08 | NULL | GPS sin place |
| 2023-10-02 14.58.15.jpg | 2023:10:02 14:58:15 | NULL | GPS sin place |
| 2023-10-02 14.58.17.jpg | 2023:10:02 14:58:17 | NULL | GPS sin place |
| 2023-10-02 14.58.20.jpg | 2023:10:02 14:58:20 | NULL | GPS sin place |

## Notas
- Escaneo sin reescritura, solo lectura exiftool y SELECT en DB.
- `ImageDescription`/`UserComment` revisados: sin residuos legacy detectados en muestra (todos vacíos en lote físico, a diferencia de 04-Abril).
- Lote físico Octubre es mayormente huérfano (0 GPS), requiere Modo Puzzle con anclas externas de `data/landmarks/dataset_roma_italia.geojson` y H3.
