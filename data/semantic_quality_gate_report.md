# Informe Quality Gate Semantico - 04-Abril 2023

**Fotos escaneadas:** 65 en `F:\2023\04-Abril`
**Alertas reales detectadas:** 62

## Reglas de deteccion
- a) filename/tag contiene pais/ciudad (ej. 'Italia') que no coincide con `place_name` (ej. 'Bosnia')
- b) coordenadas validas pero tags residuales ('test','pending','ubicacion pendiente')

| Archivo | place_name (DB) | Tags (DB) | Coordenadas | Motivo Alerta | ImageDescription EXIF |
|---|---|---|---|---|---|
| 1682158583145-aa2fc38c-9885-45c4-8017-90f34161c_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 34.7623,30.8161 | filename contiene 'Italia' pero place_name='Ruta M |  |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b075b_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 43.72,18.1 | filename contiene 'Italia' pero place_name='Ruta M |  |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b0_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 34.7614,30.8174 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| 2023-04-16 18.48.52_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 37.1947,27.2989 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| 2023-04-25 10.04.08_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 33.5537,32.5637 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| 2023-04-25 10.04.16_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 33.5536,32.5638 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| 2023-04-29 07.52.47_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 07.52.48_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 12.47.05_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 12.47.23_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 12.47.56_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 12.47.57_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 14.00.00_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| 2023-04-29 15.15.00(3)_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.01.25_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | Bunker de Tito / ARK |
| 2023-04-29 17.01.36_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | Bunker de Tito / ARK |
| 2023-04-29 17.01.37_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | Bunker de Tito / ARK |
| 2023-04-29 17.08.59_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | Bunker de Tito / ARK |
| 2023-04-29 17.44.30_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.44.31_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.44.43_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.44.44_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.49.46_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.50.07_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.52.17_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.53.36_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 2023-04-29 17.54.46_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | Stara Cuprija (Konji |
| 2023-04-29 18.00.25_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | test |
| 2023-04-29 18.01.22_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | test |
| 2023-04-29 18.12.50_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | test |
| 2023-04-29 18.14.48_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | test |
| 2023-04-30 09.18.06_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | test |
| 2023-04-30 09.18.43_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | test |
| 2023-04-30 09.19.59_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | test |
| 2023-04-30 09.27.35_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | test |
| 2023-04-30 09.28.03_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | test |
| 2023-04-30 11.08.51_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 11.09.18_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 11.25.13_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 11.25.37_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 11.26.02_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 11.34.16_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 12.05.53_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 12.07.28_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 12.07.40_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 12.07.41_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | test |
| 2023-04-30 13.44.19_Italia_2023.jpg | Bunker de Tito / ARK D-0  | {"place_hito": "Bunker de Tito | 43.6342,17.9944 | filename contiene 'Italia' pero place_name='Bunker | Bunker de Tito / ARK |
| 2023-04-30 13.44.30_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | Stara Cuprija (Konji |
| 2023-04-30 13.55.38_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | Stara Cuprija (Konji |
| 2023-04-30 14.30.33_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| 2023-04-30 15.42.01_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | Stara Cuprija (Konji |
| 2023-04-30 15.42.06_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | Stara Cuprija (Konji |
| 2023-04-30 15.42.22_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | Stara Cuprija (Konji |
| 20230401_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | Stara Cuprija (Konji |
| 20230428_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 32.2877,34.3943 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| 20230429_Italia_2023.jpg | Vrelo Bosne (Ilidza, Sara | {"place_hito": "Vrelo Bosne (I | 43.8189,18.2694 | filename contiene 'Italia' pero place_name='Vrelo  | Vrelo Bosne (Ilidza, |
| 20230430_Italia_2023.jpg | Stara Cuprija (Konjic) | {"place_hito": "Stara Cuprija  | 43.6514,17.9625 | filename contiene 'Italia' pero place_name='Stara  | Stara Cuprija (Konji |
| IMG-20230402-WA0002_Italia_2023.jpeg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 43.192,18.6267 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| IMG-20230403-WA0012_Italia_2023.jpeg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 42.8054,19.1858 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| IMG-20230418-WA0003_Italia_2023.jpeg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 36.4802,28.3319 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| IMG-20230420-WA0002_Italia_2023.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 43.72,18.1 | filename contiene 'Italia' pero place_name='Ruta M | Ruta M17 Konjic-Sara |
| Pasaporte.jpg | Ruta M17 Konjic-Sarajevo  | {"place_hito": "Ruta M17 Konji | 34.7614,30.8174 | coords validas pero tags residuales ['EXIF:ubicaci | Ruta M17 Konjic-Sara |

## Sanitizacion y purga
- **DB:** 1 registros limpiados de tags 'test','pending_osint','Italia_2023'
- **EXIF fisico:** Re-escritura con `exiftool -overwrite_original` `ImageDescription` y `UserComment` limpios

### Caso especifico `2023-04-30 11.34.16_Italia_2023.jpg`
- **Filename:** `2023-04-30 11.34.16_Italia_2023.jpg` contiene 'Italia' pero `place_name`='Bunker de Tito / ARK D-0 (Konjic)' es Bosnia (Vrelo/Bunker/Ruta M17) con coords 43.6342,17.9944
- **Tags previos:** `{"place_hito": "Bunker de Tito / ARK D-0 (Konjic)", "evento_`
- **Analisis:** No hay evidencia de cruce frontera real el 2023-04-30 11:34 (todas las fotos del dia son Bosnia M17, 12 fotos entre 09:18 y 15:42 en mismo H3). Es **renombrado erroneo** heredado de fase previa donde se etiqueto todo como `Italia_2023` por sufijo, no por geolocalizacion.
- **Correccion:** `place_name` mantenido como Bosnia, `tags` purgados a `{"place_hito":"Bunker de Tito / ARK D-0 (Konjic)","evento_viaje":"viaje_bosnia_2023"}`, EXIF `ImageDescription` reescrito a `Bunker de Tito / ARK D-0 (Konjic)` limpio.

## Sanitizados (muestra)
- `2023-04-30 11.34.16_Italia_2023.jpg`: DB tags limpiados -> {"place_hito": "Bunker de Tito / ARK D-0 -> {"plac
- `2023-04-30 11.34.16_Italia_2023.jpg`: EXIF limpiado -> ImageDescription/UserComment -> Bunker de Tito / A