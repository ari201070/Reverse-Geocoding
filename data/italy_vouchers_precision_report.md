# Reporte real de cobertura: inyección física de vouchers de Italia

**Método:** intersección de ventanas de vouchers (fechas reales del acontecimiento, horas AM/PM normalizadas a 24h) + herencia de ráfagas. Capa L3 (Ollama) excluida por servidor local caído. L0/L1/L2 únicamente.
**Lecturas:** post-escritura reales con ExifTool, sin éxitos teóricos.

## 1. Vouchers con fecha real de octubre y coordenadas válidas

| Comprobante | Ventana aplicada | Punto exacto inyectado | Coordenadas | H3 |
|---|---|---|---|---|
| Capilla Sixtina (`startDate` corregido 2023-10-01 → 2023-10-03, `14:30`) | 2023-10-03 ≥ 14:30 | Viale Vaticano, 95, 00192 Roma RM, Italia | 41.9074, 12.455 | 891e805058bffff |
| Coliseo (`02:30 PM` → `14:30:00`, `startDate` 2023-10-04) | 2023-10-04 ≥ 14:30 | Arch of Constantine, Via di S. Gregorio, Roma, Italia | 41.8898, 12.4907 | 891e80501a7ffff |

Descartados determinísticamente (sin coordenadas o fuera de Italia): `Boarding pass.pdf` (32.6475, 54.5644), `Sun Moon` (35.7507, 139.7496, fecha 2023-10-17), `DWAM-6656431` (sin coords), `Ryanair` (sin coords, solo ancla temporal), `B&B Marbò Florence` (sin coords en JSON; conserva valores Florencia existentes), `Fiumicino→Termini` (traslado, no estancia; conserva base Roma), `TripIt` (itinerario impreso, no evento).

## 2. Transacción atómica en `photo_catalog.db`

- Ventana Vaticano: 55 filas → `VOUCHER_STRICT`.
- Ventana Coliseo: 99 filas → `VOUCHER_STRICT`.
- Total `VOUCHER_STRICT`: 154 filas (lat/lng 4 decimales, `location_name` exacto del voucher, H3 res 9).
- Normalización de `date_taken` con separador `:` → `-`: 473 filas (corrige invisibilidad ante `LIKE '2023-10-%'` que ocultaba 472 filas con GPS al script `stay_open`).
- Lote octubre: 885 filas, 883 con GPS (99,77 %).
- Lagunas citadas (`14:54:16`, `14:54:25`, `14:58:20` del 2023-10-02): verificadas en disco como base Roma `41.9023, 12.5054`, motor v2.0.
- Ráfaga IMG del 2023-10-04 (`14:54:46`, `15:21:59`, etc.): verificadas en disco con bloque exacto del voucher (`41.8898, 12.4907`, H3 `891e80501a7ffff`).
- Pendientes reales sin GPS (fuera de toda ventana, sin vecino <15 min): 2 (`2023-10-29`, `2023-10-30`) → cola multimodal, no fabricados.

## 3. Inyección EXIF (`sync_exif_october_stayopen.py`, rutas absolutas)

- Ajuste del script: `ImageDescription` = nombre exacto del monumento (`location_name`), `UserComment` v2.0 con `place` exacto + `metodo VOUCHER_STRICT`; reescritura forzada de filas `VOUCHER_STRICT` aunque ya tuvieran GPS (pisa datos genéricos v1.0); modo `--only-forced` con verificación previa.
- Cobertura física JPG del lote: 861/861 con GPS; forzados `VOUCHER_STRICT`: 148/148 verificados con etiqueta `VOUCHER_STRICT` en `UserComment`.
- MP4 del lote (20 en DB, p. ej. `2023-10-03 15:41:39.mp4`): DB correcta, sin GPS físico (reescritura completa del contenedor excede el tiempo por llamada; pendiente de lote `stay_open` dedicado).

## 4. Archivos generados en esta fase

- `data/voucher_windows_oct.json`: inventario de 9 vouchers de octubre con hora normalizada 24h.
- `sync_exif_october_stayopen.py`: refactor de precisión (place exacto + forzado + `--only-forced`).
- Commits: `798931a` (parser AM/PM), `60cd978` (fechas reales Coliseo/Vaticano).
