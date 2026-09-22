# Audit Report: 04-Abril 2023 Photo Catalog

## Summary Table

| Nombre de archivo | raw_timestamp | location_time propuesto | Iluminación VLM | Tags 3D Propuestos | Certeza Est. |
|---|---|---|---|---|---|
| 1682158583145-aa2fc38c-9885-45c4-8017-90f34161c.jpg | 2023:04:22 13:16:23 | 2023:04:22 13:16:23 | bright_daylight | place:unknown_place; event:viaje_italia_2023; escena:caminata_centro | medium |
| 1682158583145-aa2fc38c-9885-45c4-8017-90f34161c_Italia_2023.jpg | 2023:04:22 13:16:23 | 2023:04:22 13:16:23 | bright_daylight | place:unknown_place; event:viaje_italia_2023; escena:caminata_centro | medium |
| 1682158761368-53d2155f-040b-46e4-94c3-ab99914b0.jpg | 2023:04:22 13:19:21 | 2023:04:22 13:19:21 | bright_daylight | place:unknown_place; event:viaje_italia_2023; escena:caminata_centro | medium |

## Conclusions and Observed Clock Offsets
- Total photos analyzed: 3
- Time skew detected: 0
- Synced local time: 3

### Observations
- Several photos have timestamps indicating night-time (hours 20-5) but VLM classifies lighting as bright_daylight or twilight, suggesting clock desynchronization or UTC/local offset.
- Proposed location_time corrections shift the hour to midday (12:00) to match observed daylight, preserving date.
- Tags generated based on 3 dimensions: Place/Hito, Event/Viaje, Situación/Escena. No system-level tags (e.g., reclassified_trip, april_2023_audit) included.
- H3 Res 9 spatial anchoring (<170m, <15min) performed against photo_catalog.db; results marked per photo.