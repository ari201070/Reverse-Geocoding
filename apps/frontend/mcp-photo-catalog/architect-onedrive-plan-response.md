Excelente. Comprendo la complejidad y la sensibilidad de la operación. Procederemos con un diseño arquitectónico robusto y una secuencia de pasos rígida, priorizando la integridad de los datos y la eficiencia.

Mi rol como "Arquitecto de Reverse Geocoding" se extiende a la gestión y optimización de datos espaciales y temporales, lo cual es crucial para la deduplicación heurística y la inferencia de metadatos.

---

### **DISEÑO DE ARQUITECTURA: "Reverse Geocoding & Consensus Truth Engine - Módulo de Gestión de Medios OneDrive"**

**Principios Arquitectónicos Aplicados:**

*   **Diseño Modular y Desacoplado:** Cada tarea compleja se descompone en módulos especializados, facilitando el desarrollo, testing y mantenimiento.
*   **Eficiencia de Datos y Soberanía Local (SpatialCache):** La base de datos `photo_catalog.db` y los discos locales F:/G: son la fuente primaria de verdad. Se minimizan las llamadas a APIs externas y las descargas innecescidas de OneDrive. El agrupamiento H3 se utilizará como un factor de deduplicación y alineación.
*   **Sinergia de Conocimiento (NotebookLM):** La estrategia se enfoca en la inferencia inteligente y la consolidación de información.
*   **Formato de Salida Interoperable:** Todas las interacciones técnicas culminarán con una instrucción clara.

---

**Componentes Modulares Propuestos:**

1.  **`OneDrive_API_Manager`:**
    *   **Responsabilidad:** Interacción segura y eficiente con la API de OneDrive (listar, descargar metadatos, descargar archivos, eliminar/mover).
    *   **Características:** Implementa el `RateLimiter` para pausas entre llamadas.
2.  **`Local_File_Scanner`:**
    *   **Responsabilidad:** Escaneo recursivo de directorios locales (F:/, G:) para identificar archivos de medios y documentos.
    *   **Características:** Extracción de metadatos básicos del sistema de archivos.
3.  **`Metadata_Extractor`:**
    *   **Responsabilidad:** Extracción de metadatos enriquecidos de archivos (EXIF para fotos/videos, fechas de creación/modificación, tamaño, nombre).
    *   **Características:** Normalización de rutas y nombres de archivo (ej. minúsculas, limpieza de prefijos "WhatsApp Image").
4.  **`Hash_Calculator`:**
    *   **Responsabilidad:** Generación de hashes criptográficos (SHA256 para coincidencia exacta) y hashes perceptuales (pHash/dHash para similitud visual).
    *   **Características:** Cálculo bajo demanda para archivos de OneDrive para evitar descargas masivas iniciales.
5.  **`Photo_Catalog_DB_Manager`:**
    *   **Responsabilidad:** Gestión de la base de datos SQLite `photo_catalog.db`.
    *   **Esquema:**
        *   `photos`: `id`, `source` (OneDrive/F/G), `original_path`, `normalized_path`, `filename`, `file_size`, `sha256_hash`, `phash`, `exif_date_taken`, `inferred_date_taken`, `last_modified_date`, `is_duplicate`, `duplicate_of_id`, `status` (pending, unique, copied_to_F, deleted_from_OneDrive, archived_OneDrive), `f_drive_path`, `latitude`, `longitude`, `h3_cell`, `geo_inference_confidence`, `geo_inferred_from`.
        *   `documents`: `id`, `source`, `original_path`, `normalized_path`, `filename`, `file_size`, `document_type`, `extracted_text`, `event_dates_json`, `extracted_locations_json` (con lat/lon/h3).
6.  **`Duplicate_Detection_Engine`:**
    *   **Responsabilidad:** Implementación del algoritmo de verificación de duplicados multi-factor.
    *   **Estrategias:** Coincidencia exacta (SHA256), coincidencia heurística (pHash, fecha, tamaño, nombre), agrupamiento H3.
7.  **`Report_Generator`:**
    *   **Responsabilidad:** Creación de informes detallados (CSV/JSON) para duplicados y acciones propuestas.
    *   **Características:** Verificación de accesibilidad de archivos "originales" en F:/G:.
8.  **`File_Operations_Manager`:**
    *   **Responsabilidad:** Ejecución segura de operaciones de archivo (copia, movimiento, eliminación) en OneDrive y discos locales.
    *   **Características:** Verificación de integridad post-copia.
9.  **`DOCX_Text_Extractor`:**
    *   **Responsabilidad:** Extracción de texto de archivos `.docx` (descomprimir ZIP, parsear XML).
    *   **Tecnología Sugerida:** Python (`zipfile`, `xml.etree.ElementTree`).
10. **`Document_Metadata_Extractor`:**
    *   **Responsabilidad:** Extracción de fechas y ubicaciones de documentos (itinerarios, reservas).
    *   **Características:** Geocodificación de ubicaciones a Lat/Lon y H3 (con `RateLimiter` para APIs externas).
11. **`Temporal_Spatial_Inference_Engine`:**
    *   **Responsabilidad:** Inferir datos geográficos para fotos sin EXIF basándose en la coincidencia temporal y espacial con documentos.
    *   **Características:** Asignación de confianza a la inferencia.
12. **`RateLimiter`:**
    *   **Responsabilidad:** Centralizar la gestión de pausas entre operaciones para evitar la saturación de APIs o sistemas.
    *   **Configuración:** Pausas de 15-30 segundos entre ejecuciones de API o bloques de operaciones intensivas.

---

### **SECUENCIA DE PASOS A SEGUIR (RÍGIDA)**

**Fase 0: Preparación y Configuración Inicial**

1.  **Configuración de Entorno:**
    *   Instalar dependencias de Python (o Node.js) para manipulación de archivos, XML, hashing, y acceso a OneDrive API.
    *   Definir credenciales de OneDrive (OAuth 2.0).
    *   Especificar rutas raíz para F:/, G: y las carpetas de OneDrive a escanear.
2.  **Inicialización de `photo_catalog.db`:**
    *   Crear la base de datos SQLite `photo_catalog.db` y sus tablas (`photos`, `documents`) si no existen, utilizando el `Photo_Catalog_DB_Manager`.
    *   Asegurar índices en campos clave como `sha256_hash`, `phash`, `inferred_date_taken`, `h3_cell`.

**Fase 1: Escaneo y Recopilación de Metadatos**

1.  **Escaneo de F:/ y G: (Local_File_Scanner):**
    *   Recorrer recursivamente las rutas F:/ y G: en busca de archivos de imagen/video y documentos.
    *   Para cada archivo:
        *   Extraer metadatos básicos (`Metadata_Extractor`: ruta, nombre, tamaño, fecha de modificación).
        *   Calcular `sha256_hash` y `phash` (`Hash_Calculator`).
        *   Extraer `exif_date_taken` (`Metadata_Extractor`).
        *   Normalizar ruta y nombre.
        *   Almacenar en `photo_catalog.db` (`photos` o `documents` tabla) con `source='F_Drive'` o `G_Drive'`.
2.  **Escaneo de OneDrive (OneDrive_API_Manager):**
    *   Utilizar `OneDrive_API_Manager` para listar recursivamente archivos de imagen/video en las carpetas designadas.
    *   Para cada archivo:
        *   Extraer metadatos básicos de la API (ruta, nombre, tamaño, fecha de modificación).
        *   Normalizar ruta y nombre.
        *   Almacenar en `photo_catalog.db` (`photos` tabla) con `source='OneDrive'`, `status='pending'`.
        *   **Aplicar `RateLimiter` (pausa de 15-30s) entre lotes de llamadas a la API de OneDrive.**
3.  **Procesamiento de Metadatos Común (Metadata_Extractor):**
    *   Para *todos* los registros de `photos` en `photo_catalog.db` (OneDrive, F:, G:):
        *   Calcular `inferred_date_taken` (prioridad: EXIF > nombre de archivo > fecha de modificación).

**Fase 2: Extracción de Documentos Clave**

1.  **Extracción de "רודוס◄ כרתים - אגיוס ניקולאוס.docx" (DOCX_Text_Extractor):**
    *   **Descarga Forzada:** Intentar descargar el archivo `.docx` de OneDrive utilizando `OneDrive_API_Manager`. Si la API falla debido a problemas de cuenta/sincronización, se debe explorar una descarga alternativa (ej. herramienta CLI de OneDrive, o si existe una copia local en caché de OneDrive).
    *   **Extracción:** Una vez descargado, usar el `DOCX_Text_Extractor` (Python):
        *   Descomprimir el archivo `.docx` (es un ZIP).
        *   Leer `word/document.xml`.
        *   Parsear el XML y extraer todo el texto plano.
        *   Limpiar el texto (eliminar tags XML, normalizar espacios).
    *   Almacenar el texto extraído en la tabla `documents` de `photo_catalog.db`, junto con la ruta original y metadatos.
    *   **Aplicar `RateLimiter` si la descarga inicial es una operación de API.**
2.  **Extracción de Metadatos de Documentos (Document_Metadata_Extractor):**
    *   Para el documento extraído y otros documentos relevantes en F:/G: (PDFs, emails, etc.):
        *   Extraer fechas de viaje, reservas, eventos.
        *   Extraer nombres de lugares (hoteles, ciudades, aeropuertos).
        *   Geocodificar estos lugares a Lat/Lon y H3 (utilizando una API externa si es necesario, con `RateLimiter` para evitar sobrecarga).
        *   Almacenar fechas y ubicaciones geocodificadas en `documents.event_dates_json` y `documents.extracted_locations_json`.

**Fase 3: Detección y Reporte de Duplicados**

1.  **Detección de Duplicados (Duplicate_Detection_Engine):**
    *   **Sub-fase 3.1: Coincidencia Exacta (SHA256):**
        *   Iterar sobre los registros de OneDrive en `photo_catalog.db` con `status='pending'`.
        *   Para cada uno, buscar coincidencias de `sha256_hash` con archivos en F:/G:.
        *   Si el `sha256_hash` del archivo de OneDrive no está calculado, el `OneDrive_API_Manager` deberá descargarlo temporalmente para calcularlo (`Hash_Calculator`).
        *   Si se encuentra una coincidencia, marcar ambos como `is_duplicate=TRUE` y registrar `duplicate_of_id`.
        *   **Aplicar `RateLimiter` (pausa de 15-30s) entre descargas de archivos de OneDrive para cálculo de hash.**
    *   **Sub-fase 3.2: Coincidencia Heurística (pHash, Fechas, Nombres, H3):**
        *   Iterar sobre los registros de OneDrive *no marcados como duplicados exactos*.
        *   Para cada uno, buscar candidatos en F:/G: basándose en:
            *   `inferred_date_taken` (coincidencia exacta o dentro de un umbral de X horas/días).
            *   `file_size` (dentro de un umbral de tolerancia).
            *   `normalized_filename` (comparación fuzzy, ej. Levenshtein).
            *   `phash` (comparación de similitud visual, umbral > 90%).
            *   **Agrupamiento H3:** Si hay datos geográficos disponibles (EXIF o inferidos), priorizar candidatos en el mismo H3 (ej. resolución 8-10) y ventana temporal.
        *   Si se encuentra una coincidencia heurística, marcar como `is_duplicate=TRUE` y `duplicate_of_id`.
        *   **Aplicar `RateLimiter` (pausa de 15-30s) si se requieren descargas adicionales para pHash.**
2.  **Generación de Informe de Duplicados (Report_Generator):**
    *   Generar un informe exhaustivo (CSV o JSON) de todos los duplicados detectados.
    *   Para cada grupo de duplicados:
        *   Listar metadatos completos de cada archivo (ruta