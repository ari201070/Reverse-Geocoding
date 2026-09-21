# Directivas Maestras de Arquitectura e Instrucciones de Agente

Este documento establece las **4 Reglas de Oro Permanentes** para el desarrollo y procesamiento en el monorrepo `Reverse-Geocoding`.

---

## 🏛️ 1. Las 4 Reglas de Oro de Arquitectura

### A. Protocolo Estricto de 2 Fases (Auditoría previa → Confirmación → Ejecución)
* **Fase 1 (Solo Lectura / Reporte):** Cualquier tarea masiva, de reorganización o de modificación debe generar primero un informe exhaustivo en consola con rutas exactas, cantidad de archivos afectados y espacio estimado en MB/GB.
* **Fase 2 (Ejecución):** Queda **terminantemente prohibido** realizar borrados físicos (`os.remove()`, `shutil.rmtree()`) o mutaciones destructivas en `data/photo_catalog.db` sin la confirmación previa y explícita del usuario.

### B. Principio de Coherencia Cinemática y "Modo Puzzle"
* **Interpolación Espacio-Temporal:** En ventanas de interpolación temporal (15 a 60 minutos), se debe aplicar un filtro de velocidad cinemática física (máximo **20–30 km/h** para visitas a pie y actividades urbanas) para evitar saltos espaciales incoherentes o "teletransportes".
* **Agrupamiento H3:** Conforma los eventos estáticos dentro de la misma celda hexagonal **H3 Resolución 9** (~170 metros).
* **Soberanía EXIF:** **Jamás** sobrescribas, modifiques o degrades coordenadas que tengan como origen `EXIF_GPS` nativo del sensor de hardware.

### C. Seguridad de Datos, Privacidad y Exclusión
* **Privacidad de Coordenadas:** Aplica siempre redondeo a **4 decimales (~11 metros)** en cualquier coordenada inyectada o calculada.
* **Lista Negra de Exclusión Obligatoria:** Los escaneos deben ignorar sistemáticamente directorios como `$RECYCLE.BIN`, `papelera`, `temp`, `.trash` y carpetas de backup duplicadas.
* **Preservación de Metadatos:** Antes de eliminar un duplicado, verifica que la copia canónica retenga igual o mayor riqueza de metadatos (EXIF/IPTC/XMP).

### D. Optimización de Rendimiento y Bloqueo de Base de Datos
* **Transacciones en Lote:** Toda operación masiva sobre SQLite debe ejecutarse agrupada en bloques (`BEGIN TRANSACTION / COMMIT` en lotes de **1,000 filas**) para evitar bloqueos de base de datos (`database locked`).
* **Fuente Única de Verdad:** `data/photo_catalog.db` es el único cerebro activo. No crear ni consultar bases de datos secundarias huérfanas.

---

## 🧭 2. Jerarquía de Señales y Descubrimiento Espacial (.skills/)

En alineación con `.agent/skills/` y `.skills/`:
1. **L0 (Cero IA - Vouchers & EXIF):** Lectura directa de pasajes, reservas de hotel y metadatos nativos EXIF con `Pillow`/`ExifTool`.
2. **L1 (Herencia Espacio-Temporal):** Vínculo por rango de fechas de itinerarios (`initialBookings.json`) y celdas H3 Res 9.
3. **L2 (Puntos de Interés Verificados):** Cruce determinista con colecciones GeoJSON (`data/landmarks/`).
4. **L3 (Visión Local de Excepción):** Análisis visual multimodal con Ollama (`moondream` / `llama3.2`) reservado exclusivamente para fotos de carteles y documentos sin geolocalización previa.
