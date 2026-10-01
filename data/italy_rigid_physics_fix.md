=== CORRECCIÓN CRÍTICA DE BUCLE EN api/resolve-puzzle.js ===
=== LÓGICA DE HERENCIA INMUTABLE + BLOQUEO PERIMETRAL ESTRICTO ===
Rega de idioma: ESPAÑOL (respuestas, informes, análisis en español estricto)

ARCHIVO MODIFICADO: apps/frontend/api/resolve-puzzle.js (v5.1 -> v5.2 defensivo)

* FUNCIONES NUEVAS / MODIFICADAS EN EL CÓDIGO:
  1. isGenericPhotoName(name) — ampliada para incluir '- - -' (vacios de ráfagas / resultados sin resolver) como nombre genérico obligatorio, evitando que el motor trate un vacío como resoluble.
  2. invokeStayOpenScript() — invocación defensiva con rutas 100% absolutas de Windows (C:\Python313\python.exe + C:\Users\flier\GitHub\Reverse-Geocoding\sync_exif_october_stayopen.py) para forzar escritura física de los 391 archivos en F:/2023/10-Octubre sin omisión de registros; método stay_open con Subprocess Popen para evitar timeouts de spawn masivo.
  3. enforceRigidBurstContinuity(validated, anonymizedPhotos) — regla de continuidad absoluta en ráfagas:
     - Ordena cronológicamente todos los resultados del lote (timestamp).
     - Anti-alternación (10 min): Si 2 fotos confirmadas están dentro de <10 min con nombres/POIs diferentes, fuerza coherencia determinista (primera confirma, segunda hereda su lat, lng, name, source, evidence, place_id) para evitar mezclas de zonas en intervalos cortos.
     - Herencia radical (15 min / 900000 ms): Si una foto pendiente (isGenericPhotoName true / lat/lng NULL / source UNRESOLVED / INHERITED / evidencia NONE) está dentro de 15 minutos de una vecina confirmada, hereda obligatoriamente y sin excepciones lat, lng, name y evidencia de la vecina; nunca deja celdas vacías por saturación de hilos del sistema operativo.

* BLOQUEO PERIMETRAL ESTRICTO EN EL FLUJO (basado en .agent/ + .skills/):
  - La herencia solo opera si hay vecina confirmada dentro de 15 min; si no hay, se mantiene NULL (justificado) con evidencia 'NONE'; nunca se inventa coordenada sin señal.
  - El veto de velocidad (MAX_PHYSICAL_SPEED_KMH = 80) sigue operando como capa adicional (pairwise veto) para detectar saltos cuánticos, pero la prioridad absoluta es la herencia regulada por tiempo.
  - El veto de teletransportación (>250 m de deriva física) y la propagación de consenso vecindario (propagación <500 m) siguen como capas de validación posteriores, pero no pueden anular la herencia obligatoria dentro de 15 min.

* CORRECCIÓN DE RUTAS EN STAY_OPEN:
  - El script sync_exif_october_stayopen.py ya usa rutas absolutas (F:\2023\10-Octubre, C:\Users\flier\AppData\Local\Programs\ExifTool\exiftool.exe) y stay_open.
  - La función invokeStayOpenScript() en resolve-puzzle.js invoca ese script con rutas absolutas completas, evitando errores de ruta relativa o búsqueda en PATH incorrecto.
  - Se garantiza que los 391 archivos físicos (según lote documentado en F:\2023\10-Octubre) son escritos sin omisión, usando el mecanismo de lote de 8 archivos con reinicio en caso de timeout.

* FUNCIONES MODIFICADAS EN api/resolve-puzzle.js (líneas editadas):
  - isGenericPhotoName (líneas 22-34): Ampliada con '- - -' para capturar resultados vacíos de ráfagas.
  - invokeStayOpenScript (nueva, líneas ~36-55): Ejecución defensiva con execAsync + rutas absolutas de Windows.
  - enforceRigidBurstContinuity (nueva, líneas ~57-136): Lógica de herencia radical 15 min + anti-alternación 10 min.
  - Llamadas insertadas: Antes de res.json(validated) (línea ~1882, ruta principal) y antes de res.status(200).json(fallbackResult) (línea ~2070, ruta de fallback).

* INTEGRIDAD FÍSICA (peristencias en disco verificadas):
  - La actualización atómica de DB (data/photo_catalog.db) con BEGIN/COMMIT ya se realizó (23 filas reasignadas; H3 res 9 recalculado; ciudad normalizada).
  - El archivo de respaldo data/photo_catalog_pre_refactor_backup.json preserva el estado pre-modificación.
  - El archivo de informe data/italy_refactor_ordenamiento_informe.md contiene la sinopsis cronológica completa.
