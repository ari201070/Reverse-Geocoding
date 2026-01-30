# Skill: ExifDataSuite

Skill especializada en el procesamiento avanzado de metadatos de imagen para aplicaciones geoespaciales.

## 🛠️ Capacidades Técnicas

### 📡 Extracción en Cascada (Cascading GPS)

Esta skill prioriza la extracción de coordenadas de múltiples fuentes para maximizar el éxito en imágenes editadas o compartidas:

1.  **EXIF nativo**: `latitude`, `longitude`.
2.  **XMP (Adobe/Google Photos)**: `GPSLatitude`, `GPSLongitude`.
3.  **IPTC Core**: Metadatos de ubicación descriptiva.

### 📅 Datación Multipunto

- Prioriza `DateTimeOriginal`.
- Fallback a `DateTime` o metadatos de sistema si es necesario.

## 🚀 Mejores Prácticas

- **Normalización**: Redondear coordenadas a 4 decimales (~11m de precisión) para optimizar la búsqueda de POIs y la privacidad (anonymization).
- **Consistencia**: Utilizar `exifr` con la opción `{ gps: true, exif: true, xmp: true }` para una vista holística.
- **Fail-safe**: Si fallan todos los metadatos, activar el flujo de geolocalización visual (Picarta AI) o manual.
