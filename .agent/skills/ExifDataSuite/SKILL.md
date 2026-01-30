# ExifDataSuite

Skill especializada en el procesamiento avanzado de metadatos de imagen para aplicaciones geoespaciales.

## Instrucciones

Esta skill debe usarse cuando el usuario necesite extraer coordenadas GPS, orientación o timestamps de fotografías de manera precisa y con fallbacks robustos.

### Herramientas Disponibles

- `extract_location_context`: Extrae lat/lng, bearing y altitude.
- `format_for_api`: Convierte coordenadas DMS a Decimal y prepara el objeto de contexto.
- `validate_exif_integrity`: Verifica la presencia de etiquetas GPS mínimas.

## Mejores Prácticas

- Utilizar `exifr` con la opción `{ gps: true }`.
- Validar siempre si las coordenadas son `0,0` (a veces indicativo de error o privacidad).
- Redondear coordenadas para búsquedas de caché de POIs (4 decimales sugerido).
