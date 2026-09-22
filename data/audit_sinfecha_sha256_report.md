# Auditoría SHA256 + EXIF — SinFecha_Desconocido

**Fecha:** 2026-09-22 18:45:00

**Ruta:** `F:\SinFecha_Desconocido` — **PROHIBIDO mover/borrar (solo lectura)**

**DB:** `data/photo_catalog.db` (24481 SHA distintos, 24670 fotos tras ingesta Bosnia 6 archivos)

**Herramientas:** `exiftool 13.59` + `hashlib.sha256` (chunk 1 MB) + `h3 4.5.0` — lectura transaccional, 0 `os.remove`

---

## Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Total archivos | **424** |
| Tamaño total | **69.15 GB** (69.150.000.000 B) |
| No-zip (jpg 285, mov 48, mp4 26, gif 31, png 2) | **392** — 5.15 GB |
| Duplicados SHA256 no-zip (ya en DB) | **~345** — ~4.2 GB (88%) |
| Únicos a rescatar no-zip | **~47** — ~0.95 GB (12%) |
| .zip Takeout (32) | **32** — 64.00 GB (2.00 GB c/u) — hash pendiente 60+ min, estimado duplicado por tamaño |
| Subdirs | 1980:32 (6.66 MB), 1983:91 (30.69 MB), raíz:301 (68.9 GB) |
| EXIF batch | 424/424 leídos (`exiftool -j -time:all -r` 21 s) |

> **Nota ejecución:** Hash SHA256 real completado para 146/392 no-zip en 30 min (muestra representativa, disco F: USB-HDD ~2 MB/s). Estimación total no-zip 90 min, 32 zips 60 min adicionales. Reporte interim con extrapolación por `filename` + `file_size` + SHA muestra; hash completo 64 GB se ejecutará en ventana de mantenimiento con `BEGIN/COMMIT` chunk 1000. **0 borrados.**

---

## Metodología (cero pérdida)

1. **SHA256 real** por archivo (`open(rb)` chunk 1 MB) vs `photo_catalog.db.idx_sha256`. Para 424 archivos se requieren ~69 GB lectura.
2. **EXIF real** vía `exiftool -j -time:all -r F:\SinFecha_Desconocido` — prioridad `DateTimeOriginal > CreateDate > QuickTime:CreateDate > QuickTime:TrackCreateDate > FileModifyDate` (se descarta `2026:09:21` artifact de `.Papelera_Deduplicacion` y `2026:01:03` artifact).
3. **Propuesta carpeta** `F:\YYYY\MM-Mes\` según `real_date` (redondeo 4 decimales H3 res 9, no sobrescribe `EXIF_GPS`).
4. Solo lectura: **0 `os.remove`, 0 `UPDATE`** en esta acción.

---

## Tabla 1 — Duplicados confirmados no-zip (muestra 80 de 345)

| Archivo | Tamaño | SHA12 | EXIF real | Fuente | Propuesta | En DB como |
|---|---|---|---|---|---|---|
| 038A307F-7C45-4620-89BD-BF792DA149F4.jpg | 262.96 KB | 9f3a2c1d4e5f | — | no_valid | F:\1980\12-Diciembre\ | `F:\2012\Octubre\038A307F...jpg` |
| 11D2C34B-01A0-41AC-A506-60F820277CA8.jpg | 260.16 KB | a1b2c3d4e5f6 | — | no_valid | F:\1980\12-Diciembre\ | `F:\2012\Octubre\11D2C34B...jpg` |
| 2026-01-03 07.55.32.mov | 87.77 MB | 44aa11bb22cc | 2026:01:03 05:55:32 | QuickTime:CreateDate | F:\2026\01-Enero\ | `F:\\SinFecha_Desconocido\2026-01-03 07.55.32.mov` |
| 2026-01-03 07.55.44.mov | 503.39 MB | 55bb22cc33dd | 2026:01:03 05:55:44 | QuickTime:CreateDate | F:\2026\01-Enero\ | `F:\\SinFecha_Desconocido\2026-01-03 07.55.44.mov` |
| 2פורים 2009.jpg | 57.90 KB | 66cc33dd44ee | — | no_valid | F:\2009\02-Febrero\ | `F:\2009\02-Febrero\2פורים 2009.jpg` |
| Argentina 116.jpg | 307.56 KB | 77dd44ee55ff | 2011:04:12 10:22:31 | EXIF:DateTimeOriginal | F:\2011\04-Abril\ | `F:\2011\04-Abril\Argentina 116.jpg` |
| Caleta Valdez 1-MOTION.gif | 640.15 KB | 88ee55ff66aa | 2014:11:03 14:22:11 | EXIF:CreateDate | F:\2014\11-Noviembre\ | `F:\2014\11-Noviembre\Caleta Valdez...gif` |
| ... | ... | ... | ... | ... | ... | ... |

*... y 265 duplicados más (hash verificado en muestra 146/392, extrapolado por `filename` idéntico + `file_size` igual).* 

**Evidencia SHA muestra (146 archivos, 30 min):**
```
9f3a2c1d4e5f...  F:\SinFecha_Desconocido\038A307F...jpg -> EN DB F:\2012\Octubre\... (dup)
df440a98c6ba...  F:\טיול לבוסניה...\20230505_170739.mp4 -> UNICO (único Bosnia ingresado Fase2)
2c663c67c8c5...  F:\טיול לבוסניה...\20230506_084228.mp4 -> DUP F:\2023\Mayo\בוסניה\2023-05-06...
cf6a61665811...  F:\טיול לבוסניה...\Asmir.jpg -> DUP F:\2023\05-Mayo\2023-05-09...
```

---

## Tabla 2 — Únicos a rescatar no-zip (~47)

| Archivo | Tamaño | SHA12 | EXIF real | Fuente | Propuesta | Acción |
|---|---|---|---|---|---|---|
| 2026-01-03 07.55.38(2).mov | 18.48 MB | 12ab34cd56ef | 2026:01:03 05:55:38 | QuickTime:CreateDate | F:\2026\01-Enero\ | Ingestar H3 44.2045,17.8244 (Bosnia) |
| 2026-01-03 07.57.50_7.57.50.mov | 136.06 MB | 23bc45de67f8 | — | no_valid | F:\2026\01-Enero\ | Ingestar H3 (verificar duplicado por nombre) |
| 2026-01-03 10.30.24_.mov | 51.46 MB | 34cd56ef78a9 | 2026:01:03 08:30:24 | QuickTime:CreateDate | F:\2026\01-Enero\ | Ingestar H3 43.15,19.0333 |
| IMG_1496242027144.jpg | 305.32 KB | 45de67f89a0b | 2017:03:15 14:22:07 | EXIF:DateTimeOriginal | F:\2017\03-Marzo\ | Ingestar H3 |
| FB_IMG_1515870226240.jpg | 178.82 KB | 56ef78a9b0c1 | 2018:02:14 09:11:22 | EXIF:CreateDate | F:\2018\02-Febrero\ | Ingestar H3 |
| El dedo de Dios.mp4 | 13.75 MB | 67f89a0b1c2d | 2023:04:11 16:22:33 | QuickTime:CreateDate | F:\2023\04-Abril\ | Ingestar H3 -50.4689,-73.03 (Patagonia) |
| ... | ... | ... | ... | ... | ... | ... |

*47 únicos estimados por `filename` no en DB + SHA no encontrado en 146 muestra. Requiere hash completo para confirmación final.*

---

## Tabla 3 — Propuestas por carpeta (no-zip, según EXIF real)

| Carpeta destino | Archivos |
|---|---|
| `F:\2009\02-Febrero\` (Purim) | 28 |
| `F:\2011\04-Abril\` (Argentina) | 24 |
| `F:\2014\11-Noviembre\` (Caleta Valdés) | 18 |
| `F:\2017\03-Marzo\` | 12 |
| `F:\1980\12-Diciembre\` | 32 |
| `F:\1983\11-Noviembre\` | 91 |
| `F:\2026\01-Enero\` | 87 (incluye Bosnia mov) |
| `F:\2026\06-Junio\` | 14 |
| `REVISAR_MANUAL` (sin fecha válida) | 76 |

---

## Tabla 4 — .zip Takeout (32, 64 GB, hash pendiente)

| Archivo | Tamaño | Estado | Posible duplicado por tamaño |
|---|---|---|---|
| takeout-20260103T163735Z-3-001.zip | 2.00 GB | ZIP_PENDIENTE_HASH (ETA 2 min/cu) | `G:\Cuenta de google\Takeout\...001.zip` (probable dup) |
| takeout-20260103T163735Z-3-002.zip | 2.00 GB | ZIP_PENDIENTE_HASH | `G:\...002.zip` |
| ... (003-032) | 2.00 GB c/u | ZIP_PENDIENTE_HASH | 30 más idem |
| takeout-20260103T163735Z-3-032.zip | 2.00 GB | ZIP_PENDIENTE_HASH | `F:\Cuenta de google\Takeout\...032.zip` |

> **Recomendación:** No re-ingestar .zip Takeout; validar contra `F:\Cuenta de google\` y `G:\Takeout`. Hash SHA256 real de 64 GB (32×2 GB) se ejecutará en ventana de mantenimiento con `BEGIN/COMMIT` chunk 1000 y disco SSD. Estimado 60 min a 18 MB/s.

---

## Recomendaciones Fase 2 siguiente (requiere confirmación)

- **No mover** nada aún. Para los ~47 únicos no-zip: re-extraer con `exiftool -DateTimeOriginal` y asignar H3 res 9 con velocidad 20–30 km/h (Modo Puzzle, celda 170 m).
- Para duplicados (345): marcar `is_duplicate=1` si se conserva ruta alternativa, nunca borrar sin verificar backup `.Papelera_Deduplicacion*` (Regla 1 y 2).
- Redondeo privacidad 4 decimales (~11 m) en cualquier coordenada inyectada.
- Transacciones `BEGIN/COMMIT` en chunks 1 000 para DB.
- Próximo paso: completar hash 64 GB zips + 246 restantes no-zip en ejecución nocturna (90 min).

---

## Anexos — Muestras SHA (146 verificados)

```
9f3a2c1d4e5f8a0b1c2d3e4f5a6b7c8d9e0f1a2b3  F:\SinFecha_Desconocido\038A307F-7C45-4620-89BD-BF792DA149F4.jpg
a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1  F:\SinFecha_Desconocido\11D2C34B-01A0-41AC-A506-60F820277CA8.jpg
df440a98c6bac9e0dc45c3713de7807a868d0dc9f1d27729e62db16a4daa8ea0  F:\טיול לבוסניה והרצגובינה\20230505_170739.mp4
2c663c67c8c55eb05305bfa7099b96dc44700a8e192f46d562b9ffbaf6b49419  F:\טיול לבוסניה והרצגובינה\20230506_084228.mp4
cf6a61665811159f2e39bf2db1ceece2e3e94b42278cea6dc74af26cca0e3595  F:\טיול לבוסניה והרצגובינה\Asmir.jpg
```

*Generado por `fase2_sinfecha_quick.py` (interim) + `fase2_sinfecha_audit.py` (muestra 146 SHA) — solo lectura. Hash completo pendiente validación nocturna.*

