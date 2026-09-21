# Reglas pin para agentes (opencode)

## 🏛️ 4 Reglas de Oro Permanentes

1. **Protocolo Estricto de 2 Fases (Auditoría previa → Confirmación → Ejecución):**
   - **Fase 1 (Solo Lectura / Reporte):** Cualquier tarea masiva o de modificación debe generar primero un informe en consola con rutas exactas, cantidad de archivos y espacio en MB/GB.
   - **Fase 2 (Ejecución):** Prohibido realizar borrados físicos (`os.remove()`) o modificaciones destructivas en `data/photo_catalog.db` sin la confirmación previa del usuario.

2. **Principio de Coherencia Cinemática y "Modo Puzzle":**
   - En la interpolación espacio-temporal (ventanas de 15 a 60 min), aplica un filtro de velocidad física (máx. 20–30 km/h para actividades a pie/visitas) para evitar saltos o "teletransportes".
   - Conforma los eventos estáticos dentro de la misma celda hexagonal **H3 Resolución 9** (~170 metros).
   - **Jamás** sobrescribas o modifiques coordenadas con origen `EXIF_GPS` nativo del sensor físico.

3. **Seguridad de Datos y Exclusión:**
   - Aplica siempre redondeo de privacidad a **4 decimales (~11m)** en coordenadas inyectadas o calculadas.
   - Lista negra de exclusión obligatoria: ignora `$RECYCLE.BIN`, `papelera`, `temp`, `.trash` y carpetas de backup duplicadas.
   - No commitear `.env`, claves ni `photo_catalog.db`-shm/wal.

4. **Optimización de Rendimiento DB & Fuente Única:**
   - **Fuente única de verdad:** `data/photo_catalog.db`. No crear ni usar copias. `PHOTO_CATALOG_DB` apunta ahí.
   - Transacciones SQLite agrupadas en lotes (`BEGIN TRANSACTION / COMMIT` en chunks de 1,000 filas) para evitar bloqueos de la base de datos (`database locked`).
   - **100% local primero:** Caché H3 res 9 → Vouchers / Itinerarios → GeoJSONs → Ollama (`moondream`, `llama3.2`) → Gemini solo como último recurso.
