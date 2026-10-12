# Informe post-reconciliación — Octubre 2023 (solo lectura + reporte)

## Cómo se resolvió el cuello de botella

El primer intento invocaba un proceso ExifTool por archivo (1287 spawns, timeout superado y transacción revertida sin daños). La versión final usa un **lote único JSON** (`exiftool -j -n -ext jpg ... F:/2023/10-Octubre`, 1257 registros en una sola llamada) y actualiza la DB en una transacción con `LIKE ... ESCAPE '/'`. Resultado: **1166 registros actualizados**, 8 filas protegidas omitidas.

## Métricas actuales (DB máster, solo lectura)

- Total octubre (`date_taken 2023-10-%` o ruta `10-Octubre`): **1310**.
- Con `place_name` válido: **1174** (antes de reconciliar: 10).
- Las 8 protegidas intactas: 6 trayecto Terravision en `NULL` con texto en tránsito, 2 cena Mercato en `NULL`.

## Tabla de estado final (Ruta Física | EXIF en F: | DB en C: | Resultado)

| Ruta Física | Estado EXIF en F: | Estado Actual en DB C: | Resultado |
|---|---|---|---|
| 2023-10-10 16.16.18_IMG_20231010_161618.jpg | GPS 45.4642, 9.1896; "Milán Centro / Stazione Centrale" | 45.4642, 9.1896, mismo texto | Sincronizado |
| 2023-10-05 17.44.42_IMG_20231005_174442.jpg | GPS 43.7698, 11.2556; "B&B Marbo Florence, Italia" | 43.7698, 11.2556, mismo texto (20 filas Marbo) | Sincronizado |
| 2023-10-02 19.16.01.jpg | GPS nativo + texto Basílica (sensor en tránsito) | `NULL` + texto Mercato (invariante visual) | Protegido, no repoblado |

## Caso testigo Santa Maria Novella

Búsqueda exhaustiva en EXIF del disco (1255 registros) y en DB: **sin menciones a Novella**. Las 20 filas del entorno dicen "B&B Marbo Florence" tanto en EXIF como, tras reconciliar, en DB. No se documenta caso Novella porque no existe en los datos; inventarlo violaría la regla de evidencia.
