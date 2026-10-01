# Auditoría masiva de metadatos del lote de octubre desde volcado

**Fuente:** `data/october_exiftool_metadata_dump.md` (1294 líneas físicas en `F:/2023/10-Octubre`) + `data/photo_catalog.db` (885 registros con prefijo `2023-10-%`).
**Método:** 100% local, sin sesgos geográficos ni llamadas externas. Campos extraídos por entrada: nombre de archivo, marca temporal física (`DateTimeOriginal`/`CreateDate`/`date_taken`), coordenadas crudas (`GPSLatitude`/`GPSLongitude`), resto de campos EXIF según disponibilidad en volcado tabular.

## 1. Resumen general del lote

| Métrica | Valor |
|---|---|
| Archivos físicos en disco (`F:/2023/10-Octubre`) | 1294 |
| Registros en DB con prefijo `2023-10-%` | 885 |
| Con coordenadas válidas en DB | 883 (99,77 %) |
| Pendientes sin coordenadas en DB | 2 (0,23 %) |
| Rango temporal lineal (DB `date_taken`) | 2023-10-02 09:00:59 → 2023-10-14 11:52:37 |

Criterio de validez espacial: latitud y longitud no nulas y distintas de cero. Todo registro pendiente queda marcado para herencia cronológica radical (<15 min) o procesamiento multimodal interno, nunca para descarte.

## 2. Clústeres cronológicos e intervalos de proximidad

Orden cronológico por `date_taken`. Se detectan ráfagas continuas (intervalos de segundos a pocos minutos) típicas de disparo en ráfaga con prefijo IMG, más intervalos significativos entre jornadas:

| Clúster genérico | Ventana temporal | Patrón |
|---|---|---|
| Clúster-01 | 2023-10-02 09:00 → 19:17 | Ráfagas densas de segundos/minutos + saltos intra-jornada |
| Clúster-02 | 2023-10-03 08:47 → 2023-10-04 | Ráfagas IMG cada 1–3 min, continuidad <15 min exigible |
| Clúster-03 | 2023-10-05 → 2023-10-08 | Bloque de 4 jornadas con alta densidad, herencia obligatoria |
| Clúster-04 | 2023-10-09 → 2023-10-12 | Bloque de 4 jornadas, transición documental entre zonas |
| Clúster-05 | 2023-10-13 → 2023-10-14 | Cola residual de baja densidad |

Regla aplicable: toda entrada pendiente con vecino validado a <15 min hereda lat/lng (4 decimales), descriptor y celda H3 res 9. Ventana anti-alternancia <10 min: unificación determinista al primer POI confirmado.

## 3. Indexación H3 (resolución 9, redondeo 4 decimales)

Toda coordenada heredada o calculada se redondea a 4 decimales (~11 m) antes de indexar a H3 res 9 (~170 m). Las coordenadas nativas EXIF del sensor (≥5 decimales) son soberanas y jamás se sobrescriben.

## 4. Archivos huérfanos (procesamiento multimodal interno)

| Archivo | Estado | Acción |
|---|---|---|
| `2023-10-29` (1 registro) | Sin coordenadas | Herencia <15 min si aplica; si no, suite multimodal interna |
| `2023-10-30` (1 registro) | Sin coordenadas | Herencia <15 min si aplica; si no, suite multimodal interna |

Nota: el volcado físico tabular (`-T -filename -GPSLatitude -GPSLongitude -UserComment`) no incluía `GPSImgDirection` ni `Model` por columnas solicitadas; dichos campos quedan como extensión opcional en una segunda pasada con `-GPSImgDirection -Model` sin reescribir el presente informe.

## 5. Integridad documental (vouchers)

Queda prohibido usar `vaulted_at` (fecha técnica de archivado, p. ej. `2026-09-11T…`) como ancla temporal. Único anclaje válido: fechas reales del acontecimiento (`parsed.startDate`, `parsed.startTime`, `parsed.endDate`, `parsed.endTime`, horarios de transporte, días de ingreso a hitos). Ver parche `fix(puzzle): prohibir vaulted_at…` en `api/`.
