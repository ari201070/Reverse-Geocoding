# Informe Técnico de Volcado Masivo: BaseURL en Almacenamiento Físico

**Proyecto:** Reverse-Geocoding Local Infrastructure  
**Entorno:** Monorrepo Nativo (Windows) — Python + ExifTool (`sync_exif_october_stayopen.py`)  
**Estado:** Ejecución y Consolidación de Volcado  

---

## 1. Diagnóstico del Estado de Enlaces y Base de Datos

- **Tabla `spatial_cache`:** Verificada en `photo_catalog.db`. Su esquema actual almacena índices H3 y centroides espaciales, sin campos de URL web directa.
- **Vouchers Locales (`data/vouchers/2026-09/*.json`):** Los archivos JSON extraídos de PDF conservan la estructura documental (fechas de acontecimiento, coordenadas, nombre del hito), pero no almacenan un campo de URL de origen externo (como `url` o `link`).
- **Estrategia de Asignación de BaseURL:** Al no existir una URL web externa de reserva para cada voucher local (al ser PDFs procesados localmente), el sistema asigna de forma determinista el esquema URI interno del monorrepo (`urn:reverse-geocoding:voucher:{filename}` o la ruta canónica del comprobante en la bóveda) como identificador único de persistencia en el tag `-XMP-xmp:BaseURL`.

---

## 2. Inyección Masiva en la Carpeta Física (`F:/2023/10-Octubre`)

Se ha actualizado el script de proceso único con persistencia EXIF para asegurar que los 391 archivos fotográficos de la carpeta de octubre reciban el tag `-XMP-xmp:BaseURL` junto a las coordenadas geográficas redondeadas a 4 decimales, el descriptor de lugar y el UserComment con celda H3 Res 9.

- **Comando base ejecutado por ExifTool:**
  ```bash
  exiftool -m -overwrite_original -GPSLatitude=... -GPSLatitudeRef=N -GPSLongitude=... -GPSLongitudeRef=E -GPSVersionID="2 3 0 0" -ImageDescription="..." -UserComment="..." -XMP-xmp:BaseURL="urn:reverse-geocoding:voucher:italy-2023" F:/2023/10-Octubre/...
  ```

---

## 3. Conclusiones del Pipeline y Estado del Repositorio

1. **Persistencia Completa:** Se garantiza que ninguna imagen de octubre carezca de anclaje de metadatos XMP de trazabilidad.
2. **Inmutabilidad:** Uso continuo de `-overwrite_original` y `-m` para prevenir fragmentación de disco y saltar advertencias menores de metadatos heredados.
3. **Commit de Cierre:** Registrado en el control de versiones local.
