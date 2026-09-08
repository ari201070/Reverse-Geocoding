# ARCHIVO DE SINCRONIZACIÓN DE ESTADO Y CONTEXTO MAESTRO (JULIO 2026)
## ATENCIÓN ARQUITECTO / OPENCODE: LEER ANTES DE ACTUAR

Este documento consolida la "Verdad del Hilo" de la conversación web para evitar regresiones lógicas y alucinaciones sobre la estructura del disco.

### 1. EL DIAGNÓSTICO REAL DEL ERROR VISUAL (COLISIÓN SQL)
* **El Problema:** El mapa de control de calidad (`generate-qa-map.js`) estaba mostrando fotos del viaje de Octubre 2025 (archivos `.heic` de la zona sur/Trelew/Gaiman) adentro de un marcador del Obelisco (CABA) correspondiente al viaje de Noviembre 2011 (`2011-11-07 12.06.53.jpg`).
* **La Causa Técnica:** No es un error de la IA de geocodificación inversa. Es un error de la consulta de agregación en la base de datos `photo_catalog.db`. La query original:
  `GROUP BY ROUND(latitude, 4), ROUND(longitude, 4), location_name`
  provocaba una **colisión de agrupación**. Al haber fotos de 2025 con `location_name` nulo, vacío o con el string genérico "Punto de Control", el `GROUP_BY` colapsaba erróneamente registros de viajes totalmente distintos bajo las coordenadas redondeadas de Buenos Aires. El `GROUP_CONCAT` mezclaba los nombres de los archivos.
* **Consecuencia del Error:** Al mezclarse en la interfaz, el mapa generaba llamadas a `/ver-foto` pidiendo imágenes del 2025 usando rutas relativas o absolutas de 2011, rompiendo el servidor con respuestas **404 (Not Found)**.

### 2. ESTRUCTURA DE RUTAS Y VERDAD DEL DISCO
* **Viaje 2011 y Viaje 2025 son INDEPENDIENTES:** Tienen itinerarios, carpetas y años distintos. No se debe asumir que comparten directorios raíz o subcarpetas cronológicas.
* **Estrategia de Indexación Novedosa:** Para mitigar los errores de rutas, `generate-qa-map.js` implementó en su backend una indexación recursiva en memoria al arrancar usando las capacidades nativas de Node (`fs.readdirSync(raiz, { recursive: true })`) mapeando los nombres de archivos a sus paths reales en `CARPETAS_RAIZ` para resolver las imágenes en tiempo de ejecución de manera ultra veloz.

### 3. REGLAS DE COMPORTAMIENTO PARA EL AGENTE (OPENCODE)
1. **Verificación Física Primero:** Prohibido asumir la existencia de carpetas. OpenCode DEBE usar sus herramientas de sistema de archivos para comprobar qué rutas existen en `C:\` y `F:\` antes de proponer código o diagnósticos.
2. **Inyección de este Contexto:** Cada vez que OpenCode invoque al Arquitecto mediante `consult_architect_llm`, debe adjuntar los puntos clave de este archivo de sincronización.
3. **Flujo de Autorización Estricto:** OpenCode debe escribir un `implementation_plan.md` y frenar su ejecución esperando la palabra "Procedé" o "Autorizado" por parte del usuario antes de modificar código.
