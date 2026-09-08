/**
 * rescue_from_papelera.mjs
 * Rescata archivos de viaje desde F:\.Papelera_Deduplicacion\ hacia sus destinos finales.
 * Estrategia de dos niveles: ruta espejada → fallback por nombre de archivo.
 * SOLO LECTURA sobre la Papelera. NO elimina ni modifica nada en ella.
 */

import fs from 'fs';
import path from 'path';

const REORG_PLAN      = './reorganization_plan.csv';
const PAPELERA_ROOT   = 'F:\\.Papelera_Deduplicacion';
const CONCURRENCY     = 2;

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (const char of line) {
    if (char === '"') inQuotes = !inQuotes;
    else if (char === ',' && !inQuotes) { result.push(current); current = ''; }
    else current += char;
  }
  result.push(current);
  return result;
}

// ─── FASE 1: Indexar toda la Papelera por nombre de archivo ───────────────────
console.log('📂 Fase 1: Indexando F:\\.Papelera_Deduplicacion\\...');
const papeleraIndex = new Map(); // filename.toLowerCase() → [fullPath, ...]

function scanDir(dir) {
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
  catch (e) { return; }
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      scanDir(fullPath);
    } else {
      const key = entry.name.toLowerCase();
      if (!papeleraIndex.has(key)) papeleraIndex.set(key, []);
      papeleraIndex.get(key).push(fullPath);
    }
  }
}

scanDir(PAPELERA_ROOT);
console.log(`   → ${papeleraIndex.size} nombres únicos indexados en la Papelera.\n`);

// ─── FASE 2: Encontrar archivos de viajes faltantes en origen ─────────────────
console.log('📖 Fase 2: Leyendo plan y detectando archivos faltantes...');
const csv = fs.readFileSync(REORG_PLAN, 'utf8');
const dataLines = csv.split('\n').filter(l => l.trim()).slice(1);

const targets = []; // { src, dst, trip }

for (const line of dataLines) {
  const parts = parseCSVLine(line);
  const src  = parts[1];
  const dst  = parts[2];
  const trip = parts[3];

  // Solo viajes (no Sin_Viaje, no encabezados)
  if (!trip || trip === 'Sin_Viaje' || trip === 'cypress' || trip === 'Chipre' || trip === 'trip') continue;

  // Solo si el origen original ya no existe
  try { fs.accessSync(src, fs.constants.F_OK); continue; } catch (_) {}

  // Solo si el destino no está ya correctamente copiado
  try {
    const dstStat = fs.statSync(dst);
    if (dstStat.size > 0) continue; // Ya existe en destino
  } catch (_) {}

  targets.push({ src, dst, trip });
}

console.log(`   → ${targets.length} archivos de viajes a rescatar.\n`);

// ─── FASE 3: Resolver ruta en Papelera para cada archivo ──────────────────────
console.log('🔍 Fase 3: Resolviendo rutas en la Papelera...');

const tasks = [];
const stats = {
  nivel1_espejado: 0,
  nivel2_por_nombre: 0,
  ambiguos: 0,
  no_encontrados: 0,
  ya_en_destino: 0,
};
const ambiguos = [];
const noEncontrados = [];

for (const { src, dst, trip } of targets) {
  const filename = path.basename(src);

  // Nivel 1: ruta espejada
  // F:\2011\Noviembre\foto.jpg → F:\.Papelera_Deduplicacion\2011\Noviembre\foto.jpg
  const relativeSrc   = src.replace(/^[A-Za-z]:\\/, '');   // "2011\Noviembre\foto.jpg"
  const mirroredPath  = path.join(PAPELERA_ROOT, relativeSrc);

  let foundPath = null;
  try {
    const st = fs.statSync(mirroredPath);
    if (st.size > 0) { foundPath = mirroredPath; stats.nivel1_espejado++; }
  } catch (_) {}

  // Nivel 2: búsqueda por nombre de archivo
  if (!foundPath) {
    const candidates = papeleraIndex.get(filename.toLowerCase()) || [];
    if (candidates.length === 1) {
      const st = fs.statSync(candidates[0]);
      if (st.size > 0) { foundPath = candidates[0]; stats.nivel2_por_nombre++; }
    } else if (candidates.length > 1) {
      stats.ambiguos++;
      ambiguos.push({ filename, trip, dst, candidates });
      continue;
    } else {
      stats.no_encontrados++;
      noEncontrados.push({ filename, trip, dst, src_original: src });
      continue;
    }
  }

  tasks.push({ src: foundPath, dst, trip });
}

console.log(`   ✅ Nivel 1 (ruta espejada):      ${stats.nivel1_espejado}`);
console.log(`   ✅ Nivel 2 (búsqueda por nombre): ${stats.nivel2_por_nombre}`);
console.log(`   ⚠️  Ambiguos (no se tocan):        ${stats.ambiguos}`);
console.log(`   ❌ No encontrados:                 ${stats.no_encontrados}`);
console.log(`\n🚀 Total de archivos a copiar: ${tasks.length}\n`);

if (tasks.length === 0) {
  console.log('🎉 No hay nada que copiar.');
  process.exit(0);
}

// ─── FASE 4: Copia con concurrencia controlada ────────────────────────────────
const createdDirs = new Set();

async function ensureDir(dirPath) {
  if (createdDirs.has(dirPath)) return;
  await fs.promises.mkdir(dirPath, { recursive: true });
  createdDirs.add(dirPath);
}

async function processQueue(tasks, limit) {
  let index = 0, active = 0, success = 0, errors = 0;
  const errorLog = [];

  return new Promise(resolve => {
    function next() {
      if (index >= tasks.length && active === 0) {
        resolve({ success, errors, errorLog });
        return;
      }
      while (active < limit && index < tasks.length) {
        active++;
        const task = tasks[index++];
        const dstDir = path.dirname(task.dst);

        ensureDir(dstDir)
          .then(() => fs.promises.copyFile(task.src, task.dst))
          .then(() => {
            success++;
            if (success % 50 === 0 || success === tasks.length) {
              console.log(`  ➡️  ${success}/${tasks.length} rescatados... [trip: ${task.trip}]`);
            }
          })
          .catch(err => {
            errors++;
            errorLog.push({ file: path.basename(task.dst), trip: task.trip, error: err.message });
            console.error(`  [ERROR] ${path.basename(task.src)}: ${err.message}`);
          })
          .finally(() => { active--; next(); });
      }
    }
    next();
  });
}

console.log(`⚙️  Iniciando rescate con concurrencia ${CONCURRENCY}...`);
const result = await processQueue(tasks, CONCURRENCY);

// ─── FASE 5: Reporte final ────────────────────────────────────────────────────
const report = {
  resumen: {
    targets_identificados: targets.length,
    nivel1_espejado: stats.nivel1_espejado,
    nivel2_por_nombre: stats.nivel2_por_nombre,
    copiados_exitosamente: result.success,
    errores_copia: result.errors,
    ambiguos_no_tocados: stats.ambiguos,
    no_encontrados: stats.no_encontrados,
  },
  errores_copia: result.errorLog,
  ambiguos,
  no_encontrados: noEncontrados,
};

fs.writeFileSync('rescue_report.json', JSON.stringify(report, null, 2));

console.log('\n========================================');
console.log('🎉 RESCATE FINALIZADO');
console.log('========================================');
console.log(`✅ Copiados exitosamente:  ${result.success}`);
console.log(`⚠️  Ambiguos (no tocados): ${stats.ambiguos}`);
console.log(`❌ No encontrados:         ${stats.no_encontrados}`);
console.log(`❌ Errores de copia:       ${result.errors}`);
console.log('========================================');
console.log('📄 Reporte completo en rescue_report.json');
