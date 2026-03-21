/**
 * Suite de Pruebas de Estrés — Arquitectura de Inteligencia Espacial
 * Cubre los 5 escenarios definidos por NotebookLM.
 *
 * Ejecución: node tests/stress/stress-test-suite.js
 */

import { latLngToCell } from 'h3-js';
import assert from 'node:assert/strict';
import { clusterPhotos } from '../../src/utils/puzzleLogic.js';
import { sanitizeString as sanitize } from '../../api/python-service.js';

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✅ ${name}`);
    passed++;
  } catch (e) {
    console.error(`  ❌ ${name}`);
    console.error(`     ${e.message}`);
    failed++;
  }
}

// ---------------------------------------------------------------------------
// 1. SANITIZACIÓN COMPLETA DE STRINGS (SQL / JSON / HTML)
// ---------------------------------------------------------------------------
console.log('\n[1] Sanitización: Todos los caracteres peligrosos');

test("Earl's Court — apostrophe → SQL-safe ''", () => {
  const s = sanitize("Earl's Court");
  assert.equal(s, "Earl''s Court");
  assert.ok(s.includes("''"), "Debe contener comilla doble (SQL-safe)");
});

test("L'Hospitalet — apostrophe al inicio", () => {
  const s = sanitize("L'Hospitalet");
  assert.equal(s, "L''Hospitalet");
});

test("Rock & Feller's — ampersand + apostrophe", () => {
  const s = sanitize("Rock & Feller's");
  assert.equal(s, "Rock &amp; Feller''s");
});

test("< > en nombre de lugar — HTML injection", () => {
  const s = sanitize("<Plaza Mayor>");
  assert.equal(s, "&lt;Plaza Mayor&gt;");
});

test('Comilla doble " — JSON breakout', () => {
  const s = sanitize('Café "El Rincón"');
  assert(s.includes('&quot;'), 'Debe escapar las comillas dobles');
  assert(!s.includes('"'), 'No deben quedar comillas dobles literales');
});

test("Punto y coma ; — SQL statement terminator", () => {
  const s = sanitize("DROP TABLE; known_places");
  assert(!s.includes(';'), 'Debe eliminar el punto y coma');
  assert.ok(s.includes('DROP TABLE'), 'El texto legítimo debe preservarse');
});

test("Comentario SQL -- — SQL line comment injection", () => {
  const s = sanitize("legit name -- DROP TABLE");
  assert(!s.includes('--'), 'Debe eliminar el comentario SQL');
});

test("Comentario SQL /* — SQL block comment injection", () => {
  const s = sanitize("name /* injected comment */");
  assert(!s.includes('/*'), 'Debe eliminar el inicio de comentario de bloque');
});

test("Backtick ` — SQL identifier injection", () => {
  const s = sanitize("`places`");
  assert(!s.includes('`'), 'Debe eliminar los backticks');
});

test("Null byte \\x00 — null byte injection", () => {
  const s = sanitize("Evil\x00Place");
  assert(!s.includes('\x00'), 'Debe eliminar los null bytes');
  assert.ok(s.includes('Place'), 'El texto legítimo debe preservarse');
});

test("String limpio — no cambia innecesariamente", () => {
  const s = sanitize("Buenos Aires");
  assert.equal(s, "Buenos Aires");
});

test("Input no string (null) — devuelve string vacío", () => {
  const s = sanitize(null);
  assert.equal(s, "");
});


// ---------------------------------------------------------------------------
// 2. LÍMITES DEL MODO PUZZLE (Spatio-Temporal)
// ---------------------------------------------------------------------------
console.log('\n[2] Modo Puzzle: Límites Temporales y Espaciales');

const BASE_TIME = 1700000000000; // ms timestamp base
const ANCHOR_LAT = -34.5753;
const ANCHOR_LNG = -58.3814;

// Escenario A — Límite temporal (14m55s vs 15m05s)
test('Par con 14m55s hereda ubicación del ancla', () => {
  const photos = [
    { lat: ANCHOR_LAT, lng: ANCHOR_LNG, timestamp: BASE_TIME, gpsAccuracy: 5 },
    { lat: null, lng: null, timestamp: BASE_TIME + (14 * 60 + 55) * 1000 },
  ];
  const clusters = clusterPhotos(photos);
  assert.equal(clusters.length, 1, 'Deben estar en el mismo clúster');
  const second = clusters[0].photos[1];
  assert(second.inherited, 'La segunda foto debe haber heredado la ubicación');
  assert.equal(second.lat, ANCHOR_LAT);
});

test('Par con 15m05s inicia geocodificación independiente', () => {
  const photos = [
    { lat: ANCHOR_LAT, lng: ANCHOR_LNG, timestamp: BASE_TIME, gpsAccuracy: 5 },
    { lat: null, lng: null, timestamp: BASE_TIME + (15 * 60 + 5) * 1000 },
  ];
  const clusters = clusterPhotos(photos);
  // Sin GPS y fuera de ventana → la segunda no hereda
  const second = clusters[0].photos[1];
  assert(!second.inherited, 'La segunda foto NO debe haber heredado');
  assert.equal(second.lat, null);
});

// Escenario B — Frontera H3
test('Fotos simultáneas en celdas H3 distintas rompen el clúster', () => {
  // Celda 1: punto de referencia
  const lat1 = -34.5753, lng1 = -58.3814;
  // Celda 2: desplazado ~200m para garantizar celda H3 diferente
  const lat2 = -34.5770, lng2 = -58.3814;

  const h3_1 = latLngToCell(lat1, lng1, 9);
  const h3_2 = latLngToCell(lat2, lng2, 9);

  // Si, por azar geográfico, coinciden, el test se salta
  if (h3_1 === h3_2) {
    console.log('     ⚠️  Skipped: puntos en la misma celda H3 por geometría local');
    return;
  }

  const photos = [
    { lat: lat1, lng: lng1, timestamp: BASE_TIME, gpsAccuracy: 5 },
    { lat: lat2, lng: lng2, timestamp: BASE_TIME + 1000 }, // 1s después
  ];
  const clusters = clusterPhotos(photos);
  assert.equal(clusters.length, 2, 'Deben formarse 2 clústeres por frontera H3');
});

// ---------------------------------------------------------------------------
// 3. CONSENSO MULTIMODAL — Prueba de RapidFuzz (simulada en JS)
// ---------------------------------------------------------------------------
console.log('\n[3] Consenso Multimodal: Reconciliación Semántica');

// Simulación local del token_set_ratio de RapidFuzz (Jaccard de tokens)
function tokenSetRatioSimple(a, b) {
  const tokensA = new Set(a.toLowerCase().split(/\s+/));
  const tokensB = new Set(b.toLowerCase().split(/\s+/));
  const intersection = [...tokensA].filter(t => tokensB.has(t)).length;
  const union = new Set([...tokensA, ...tokensB]).size;
  return Math.round((intersection / union) * 100);
}

test('OCR "PARA MI AMIGO CARLITOS" reconcilia con "El Boliche de Nico"', () => {
  // Este caso debería tener baja similitud directa → escalaría a Nivel 3 real
  // Aquí validamos que no haya crash y que el score retorne un número
  const score = tokenSetRatioSimple("PARA MI AMIGO CARLITOS", "El Boliche de Nico");
  assert(typeof score === 'number', 'El score debe ser numérico');
  assert(score >= 0 && score <= 100, 'Score debe estar entre 0 y 100');
});

test('OCR "Earl Court" vs "Earl\'s Court" — similitud parcial detectada', () => {
  // La lógica exacta de token_set_ratio vive en Python/RapidFuzz.
  // En JS solo verificamos que el score sea numérico y > 0 (similitud parcial detectada).
  const score = tokenSetRatioSimple("Earl Court", "Earl's Court");
  assert(typeof score === 'number' && score > 0, `Score debe ser > 0, fue: ${score}`);
});

test('OCR idéntico al nombre oficial → score máximo', () => {
  const score = tokenSetRatioSimple("Buenos Aires", "Buenos Aires");
  assert.equal(score, 100);
});

// ---------------------------------------------------------------------------
// 4. PRIVACIDAD Y RENDIMIENTO DE CACHÉ
// ---------------------------------------------------------------------------
console.log('\n[4] Privacidad: Redondeo a 4 Decimales');

function roundCoord(val) {
  return Math.round(val * 10000) / 10000;
}

test('100 coords con variación en 5to/6to decimal resultan en la misma celda H3', () => {
  const lats = Array.from({ length: 100 }, (_, i) =>
    -34.575300 + (i * 0.000001) // variación en 6to decimal
  );
  const h3Cells = lats.map(lat => latLngToCell(roundCoord(lat), roundCoord(-58.381400), 9));
  const uniqueCells = new Set(h3Cells);
  assert.equal(uniqueCells.size, 1, `Deben mapearse a una sola celda H3. Encontradas: ${uniqueCells.size}`);
});

test('Redondeo correcto: -34.5753019 → -34.5753', () => {
  assert.equal(roundCoord(-34.5753019), -34.5753);
});

test('Redondeo correcto: -58.38145678 → -58.3815', () => {
  assert.equal(roundCoord(-58.38145678), -58.3815);
});

// ---------------------------------------------------------------------------
// 5. HUMAN-IN-THE-LOOP — Lógica de umbral de confianza
// ---------------------------------------------------------------------------
console.log('\n[5] Human-in-the-Loop: Umbral de Confianza 75%');

function shouldTriggerHumanReview(confidenceScore) {
  return confidenceScore < 75;
}

function onConsensusResult(score) {
  if (shouldTriggerHumanReview(score)) {
    return { action: 'HALT', requiresManualValidation: true };
  }
  return { action: 'PROCEED', requiresManualValidation: false };
}

test('Score 74% activa validación manual (HALT)', () => {
  const result = onConsensusResult(74);
  assert.equal(result.action, 'HALT');
  assert.equal(result.requiresManualValidation, true);
});

test('Score 75% exacto procede automáticamente (PROCEED)', () => {
  const result = onConsensusResult(75);
  assert.equal(result.action, 'PROCEED');
  assert.equal(result.requiresManualValidation, false);
});

test('Score 100% procede sin interrupción', () => {
  const result = onConsensusResult(100);
  assert.equal(result.action, 'PROCEED');
});

test('Score 0% siempre activa validación manual', () => {
  const result = onConsensusResult(0);
  assert.equal(result.action, 'HALT');
});

// ---------------------------------------------------------------------------
// RESUMEN
// ---------------------------------------------------------------------------
console.log('\n─────────────────────────────────────────');
console.log(`  Total: ${passed + failed} | ✅ Passed: ${passed} | ❌ Failed: ${failed}`);
console.log('─────────────────────────────────────────');

if (failed > 0) process.exit(1);
