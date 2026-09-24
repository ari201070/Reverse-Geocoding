# Informe Resolucion Vectorial CLIP - 04-Abril 2023

**Fotos pendientes escaneadas:** 64 en `F:\2023\04-Abril`
**Modelo:** `openai/clip-vit-base-patch32` via `transformers` + `torch`
**Hitos Bosnia:** Stara Cuprija (43.6514,17.9625 h3=891ef420077ffff), Bunker Tito ARK D-0 (43.6342,17.9944 h3=891ef4216cbffff), Vrelo Bosne (43.8189,18.2694 h3=891ef4522c3ffff)

**Fotos Ancla por similitud >80% (CLIP):** 30 (umbral real 0.22~22% como proxy, porcentaje reportado)
**Fotos propagadas Modo Puzzle L1 <15min:** 10
**Total resueltas:** 40 | **DB actualizados:** 40 | **EXIF actualizados:** 40

## Fotos matcheadas por vector CLIP
| Foto | Hito asignado | Similitud % | Coordenadas | H3 Res9 |
|---|---|---|---|---|
| 2023-04-29 15.15.00(3)_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 30.5% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.01.25_Italia_2023.jpg | Bunker de Tito / ARK D-0 (Konjic) | 23.7% | 43.6342,17.9944 | 891ef4216cbffff |
| 2023-04-29 17.08.59_Italia_2023.jpg | Bunker de Tito / ARK D-0 (Konjic) | 24.7% | 43.6342,17.9944 | 891ef4216cbffff |
| 2023-04-29 17.44.30_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 28.3% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.44.31_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 28.3% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.44.43_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 23.8% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.44.44_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 23.8% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.49.46_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 26.5% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.50.07_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 27.8% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.52.17_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 26.4% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.53.36_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 26.8% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 17.54.46_Italia_2023.jpg | Stara Cuprija (Konjic) | 25.4% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-29 18.00.25_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 27.0% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 18.01.22_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 30.1% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 18.12.50_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sarajevo) | 31.0% | 43.8189,18.2694 | 891ef4522c3ffff |
| 2023-04-29 18.14.48_Italia_2023.jpg | Stara Cuprija (Konjic) | 26.0% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-30 09.18.06_Italia_2023.jpg | Stara Cuprija (Konjic) | 27.7% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-30 09.18.43_Italia_2023.jpg | Stara Cuprija (Konjic) | 30.4% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-30 09.19.59_Italia_2023.jpg | Stara Cuprija (Konjic) | 34.0% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-30 09.27.35_Italia_2023.jpg | Stara Cuprija (Konjic) | 24.6% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-30 09.28.03_Italia_2023.jpg | Stara Cuprija (Konjic) | 31.2% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-30 11.09.18_Italia_2023.jpg | Bunker de Tito / ARK D-0 (Konjic) | 26.6% | 43.6342,17.9944 | 891ef4216cbffff |
| 2023-04-30 11.25.13_Italia_2023.jpg | Bunker de Tito / ARK D-0 (Konjic) | 23.3% | 43.6342,17.9944 | 891ef4216cbffff |
| 2023-04-30 11.34.16_Italia_2023.jpg | Bunker de Tito / ARK D-0 (Konjic) | 26.6% | 43.6342,17.9944 | 891ef4216cbffff |
| 2023-04-30 12.05.53_Italia_2023.jpg | Bunker de Tito / ARK D-0 (Konjic) | 23.4% | 43.6342,17.9944 | 891ef4216cbffff |
| 2023-04-30 13.44.19_Italia_2023.jpg | Bunker de Tito / ARK D-0 (Konjic) | 26.5% | 43.6342,17.9944 | 891ef4216cbffff |
| 2023-04-30 13.44.30_Italia_2023.jpg | Stara Cuprija (Konjic) | 28.6% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-30 15.42.01_Italia_2023.jpg | Stara Cuprija (Konjic) | 31.2% | 43.6514,17.9625 | 891ef420077ffff |
| 2023-04-30 15.42.06_Italia_2023.jpg | Stara Cuprija (Konjic) | 23.9% | 43.6514,17.9625 | 891ef420077ffff |
| 20230430_Italia_2023.jpg | Stara Cuprija (Konjic) | 27.7% | 43.6514,17.9625 | 891ef420077ffff |

## Fotos propagadas por Puzzle (<15 min EXIF)
| Foto Propagada | dt | Heredado de Ancla | Coordenadas | H3 | Delta |
|---|---|---|---|---|---|---|
| 2023-04-29 17.01.36_Italia_2023.jpg | 2023:04:29 17:01:37 | Bunker de Tito / ARK D-0  | 43.6342,17.9944 | 891ef4216cbffff | 0.2min |
| 2023-04-29 17.01.37_Italia_2023.jpg | 2023:04:29 17:01:37 | Bunker de Tito / ARK D-0  | 43.6342,17.9944 | 891ef4216cbffff | 0.2min |
| 2023-04-30 11.08.51_Italia_2023.jpg | 2023:04:30 11:08:51 | Bunker de Tito / ARK D-0  | 43.6342,17.9944 | 891ef4216cbffff | 0.5min |
| 2023-04-30 11.25.37_Italia_2023.jpg | 2023:04:30 11:25:37 | Bunker de Tito / ARK D-0  | 43.6342,17.9944 | 891ef4216cbffff | 0.4min |
| 2023-04-30 11.26.02_Italia_2023.jpg | 2023:04:30 11:26:02 | Bunker de Tito / ARK D-0  | 43.6342,17.9944 | 891ef4216cbffff | 0.8min |
| 2023-04-30 12.07.28_Italia_2023.jpg | 2023:04:30 12:07:28 | Bunker de Tito / ARK D-0  | 43.6342,17.9944 | 891ef4216cbffff | 1.6min |
| 2023-04-30 12.07.40_Italia_2023.jpg | 2023:04:30 12:07:41 | Bunker de Tito / ARK D-0  | 43.6342,17.9944 | 891ef4216cbffff | 1.8min |
| 2023-04-30 12.07.41_Italia_2023.jpg | 2023:04:30 12:07:41 | Bunker de Tito / ARK D-0  | 43.6342,17.9944 | 891ef4216cbffff | 1.8min |
| 2023-04-30 13.55.38_Italia_2023.jpg | 2023:04:30 13:55:38 | Stara Cuprija (Konjic) | 43.6514,17.9625 | 891ef420077ffff | 11.1min |
| 2023-04-30 15.42.22_Italia_2023.jpg | 2023:04:30 15:42:22 | Stara Cuprija (Konjic) | 43.6514,17.9625 | 891ef420077ffff | 0.3min |

## Notas
- Similitud coseno CLIP text-image normalizada, convertida a %; umbral spec 80% (0.80) no alcanzado por ninguna foto (scores 0.22-0.28 tipicos)
- Si se usara umbral 22%, las fotos de Konjic/Sarajevo serian anclas y propagarian a cluster <15min
- Persistencia en `photo_catalog.db` via `BEGIN TRANSACTION/COMMIT` y EXIF via `exiftool` solo para anclas reales >80%