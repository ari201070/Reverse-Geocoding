# Blueprint Operativo - Fase 2: Visualización de Calidad (QA) y Escaneo de Filenames Global

## Objetivos
1. Crear una herramienta local de validación visual (Mapa interactivo) para el usuario.
2. Extender la heurística de extracción por nombre de archivo (`HEURISTICA_FILENAME`) a todo el catálogo histórico de la base de datos.

## Instrucciones para OpenCode (Ejecución Autónoma)

### Tarea 1: Generador del Mapa de Validación Visual (`api/generate-qa-map.js`)
Crea un script en Node.js que realice lo siguiente:
- Conéctese a `photo_catalog.db`.
- Extraiga todas las fotos que tengan `latitude` y `longitude` válidas, agrupándolas por su `location_name` o por cercanía (redondeo a 2 decimales para clusterizar).
- Genere un archivo HTML autónomo en la raíz del proyecto llamado `api/mapa_control_calidad.html`.
- Este HTML debe cargar **Leaflet.js** (vía CDN público) y dibujar marcadores interactivos (pins o círculos) por cada cluster de fotos detectado. Al hacer clic en un pin, debe mostrar el nombre del lugar, la cantidad de fotos asignadas y un ejemplo de `metadata_source`.
- Al finalizar, imprímete la ruta del archivo para que Ari pueda hacerle doble clic y visualizar su catálogo.

### Tarea 2: Escaneo Global de Patrones en Nombres de Archivo
- Modifica el script de análisis para que busque patrones geográficos explícitos en el campo `filename` de **todas** las fotos que aún permanecen con `latitude IS NULL` en el catálogo completo (las ~27,283 restantes).
- Aplica el regex validado para capturar cadenas entre paréntesis o palabras clave de las 12 ubicaciones ya conocidas.
- Inyecta las coordenadas correctas del diccionario de calidad en formato transaccional y ejecuta la repropagación temporal por bloques de tiempo.

## Reporte de Salida
- Actualiza el final de este archivo `api/blueprint.md` indicando:
  1. Si el mapa HTML fue generado con éxito.
  2. Cuántas nuevas fotos ancla fueron rescatadas a nivel global gracias al escaneo completo del catálogo.
