# Protocolo de Arquitectura Integrada Ligera para CPU

1. **Lectura Directa de Vouchers y Pasajes (L0 - Cero IA):**
   - Para archivos `.pkpass`: Descomprimir como ZIP con `zipfile` y leer el archivo `pass.json` nativo.
   - Para imágenes de códigos QR: Decodificar con `pyzbar` / `opencv` sin pasar por modelos de visión.
   - Para metadatos EXIF: Extraer fecha y coordenadas nativas con `Pillow` / `exiftool`.

2. **Herencia por Itinerario y Documentos en DB (L1 - Sincronización):**
   - Antes de procesar cualquier foto sin GPS, consultar `notebooklm-mcp` o las reservas en `photo_catalog.db` para obtener el rango de fechas.
   - Aplicar el `CITY_FALLBACK` (centroide de ciudad) y la herencia espacio-temporal (±15 min en celdas H3 Res 9) a las fotos de `comida`, `retrato` e `interiores`.

3. **OCR / Visión de Excepción (L2 - Únicamente Fotos Ancla):**
   - Reservar el análisis por visión artificial (Ollama / Florence-2 / PaddleOCR) **exclusivamente** para fotos clasificadas como carteles o documentos que no tengan herencia de voucher.
   - Redimensionar siempre las fotos a 1024px antes de enviarlas al modelo.

4. **Prohibiciones:**
   - Prohibido usar `Glob` o búsquedas recursivas en disco sin ruta previa desde DB.
   - Prohibido crear archivos HTML sueltos en las carpetas de fotos del disco F:.
   - Prohibido correr modelos de visión de 7B/13B en bucle sobre lotes masivos.
