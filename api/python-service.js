/**
 * Módulo de integración: Orquestador Node.js → Microservicio Python.
 * Responsable de invocar los endpoints del microservicio Python de forma segura.
 */

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://localhost:8080';

/**
 * Sanitización centralizada de strings antes de cualquier consulta SQL/JSON.
 * Cubre todos los caracteres problemáticos conocidos:
 *   '  → ''          (SQL injection via apostrophe - "Earl's Court")
 *   &  → &amp;       (HTML entity injection - "Rock & Feller's")
 *   <  → &lt;        (HTML/XML injection)
 *   >  → &gt;        (HTML/XML injection)
 *   "  → &quot;      (JSON breakout)
 *   ;  → (removed)   (SQL statement terminator)
 *   -- → (removed)   (SQL comment)
 *   /* → (removed)   (SQL block comment start)
 *   `  → (removed)   (SQL backtick identifier injection)
 *   \0 → (removed)   (null byte injection)
 */
export function sanitizeString(str) {
  if (typeof str !== 'string') return '';
  return str
    // 1. Eliminar primero los caracteres SQL peligrosos (antes de codificar entidades)
    .replace(/\x00/g, '')          // null bytes
    .replace(/;/g, '')             // SQL statement terminator
    .replace(/--/g, '')            // SQL line comment
    .replace(/\/\*/g, '')          // SQL block comment start
    .replace(/`/g, '')             // backtick identifier injection
    // 2. Escapar apostrophe para SQL (duplicar, no eliminar)
    .replace(/'/g, "''")           // apostrophe → SQL-safe ''
    // 3. Codificar entidades HTML/JSON (semicolons ya no están en el string)
    .replace(/&/g, '&amp;')        // ampersand → &amp;
    .replace(/</g, '&lt;')         // less-than → &lt;
    .replace(/>/g, '&gt;')         // greater-than → &gt;
    .replace(/"/g, '&quot;');      // double quote → &quot;
}

/**
 * Verifica que el microservicio Python esté operativo.
 */
async function checkHealth() {
  const res = await fetch(`${PYTHON_SERVICE_URL}/health`);
  return res.ok;
}

/**
 * Envía una imagen al microservicio para extraer metadatos EXIF/GPS.
 * @param {Buffer} imageBuffer - Bytes del archivo de imagen.
 * @returns {{ lat, lng, timestamp, gps_accuracy }}
 */
async function analyzeExif(imageBuffer) {
  const formData = new FormData();
  formData.append('image', new Blob([imageBuffer]), 'photo.jpg');

  const res = await fetch(`${PYTHON_SERVICE_URL}/analyze-exif`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error(`EXIF service error: ${res.status}`);
  return res.json();
}

/**
 * Reconcilia texto OCR contra un nombre oficial usando RapidFuzz en Python.
 * @param {string} ocrText - Fragmento detectado por OCR.
 * @param {string} officialName - Nombre oficial de la API.
 * @returns {{ score: number, match: boolean }}
 */
async function reconcileName(ocrText, officialName) {
  const res = await fetch(`${PYTHON_SERVICE_URL}/reconcile-name`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // Sanitización centralizada: cubre apóstrofes, &, <, >, ", ; y otros
    body: JSON.stringify({
      ocr_text: sanitizeString(ocrText),
      official_name: sanitizeString(officialName),
    }),
  });

  if (!res.ok) throw new Error(`Reconciliation service error: ${res.status}`);
  return res.json();
}

export { checkHealth, analyzeExif, reconcileName };
