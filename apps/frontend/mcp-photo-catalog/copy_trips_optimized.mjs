import fs from 'fs';
import path from 'path';

const REORG_PLAN = './reorganization_plan.csv';
const CONCURRENCY_LIMIT = 2; // Optimizado para HDD mecánico

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') inQuotes = !inQuotes;
    else if (char === ',' && !inQuotes) { result.push(current); current = ''; }
    else current += char;
  }
  result.push(current);
  return result;
}

const createdDirs = new Set();

async function ensureDirExists(dirPath) {
  if (createdDirs.has(dirPath)) return;
  await fs.promises.mkdir(dirPath, { recursive: true });
  createdDirs.add(dirPath);
}

// 1. Leer CSV
console.log('📖 Leyendo plan de reorganización...');
const csv = fs.readFileSync(REORG_PLAN, 'utf8');
const lines = csv.split('\n').filter(l => l.trim());
const dataLines = lines.slice(1);

// Filtrar viajes a procesar
const tripLines = dataLines.filter(l => {
  const parts = parseCSVLine(l);
  const trip = parts[3];
  return trip && trip !== 'Sin_Viaje' && trip !== 'cyprus' && trip !== 'Chipre' && trip !== 'trip';
});

console.log(`📋 Total en plan (sin 'Sin_Viaje'): ${tripLines.length} archivos.`);

// 2. Preparar tareas
let pendingTasks = [];
let completadosYa = 0;
let faltantesOrigen = 0;
let tasksByTrip = {};

console.log('🔍 Validando estado actual en disco...');

for (let i = 0; i < tripLines.length; i++) {
  const parts = parseCSVLine(tripLines[i]);
  const src = parts[1];
  const dst = parts[2];
  const trip = parts[3];
  
  if (!tasksByTrip[trip]) {
    tasksByTrip[trip] = { total: 0, copied: 0, failed: 0 };
  }

  let srcSize = -1;
  try {
    srcSize = fs.statSync(src).size;
  } catch (e) {
    faltantesOrigen++;
    continue;
  }

  let dstSize = -1;
  try {
    dstSize = fs.statSync(dst).size;
  } catch (e) {
  }

  if (dstSize === srcSize) {
    completadosYa++;
    tasksByTrip[trip].copied++;
  } else {
    tasksByTrip[trip].total++;
    pendingTasks.push({ src, dst, trip });
  }
}

console.log(`✅ Archivos ya en destino (intactos): ${completadosYa}`);
console.log(`❌ Archivos faltantes en origen: ${faltantesOrigen}`);
console.log(`🚀 Archivos PENDIENTES por copiar: ${pendingTasks.length}\n`);

if (pendingTasks.length === 0) {
  console.log('🎉 Todo está listo. No hay nada que copiar.');
  process.exit(0);
}

// 3. Ejecutar copias con flujo controlado
async function processQueue(tasks, limit) {
  let active = 0;
  let index = 0;
  let success = 0;
  let errors = 0;
  
  return new Promise((resolve) => {
    function next() {
      if (index >= tasks.length && active === 0) {
        resolve({ success, errors });
        return;
      }
      
      while (active < limit && index < tasks.length) {
        active++;
        const task = tasks[index++];
        const dstDir = path.dirname(task.dst);
        
        ensureDirExists(dstDir)
          .then(() => fs.promises.copyFile(task.src, task.dst))
          .then(() => {
            success++;
            tasksByTrip[task.trip].copied++;
            if (success % 50 === 0 || success === tasks.length) {
              console.log(`  ➡️ Progreso general: ${success}/${tasks.length} copiados... [Último: ${task.trip}]`);
            }
          })
          .catch(err => {
            errors++;
            tasksByTrip[task.trip].failed++;
            console.error(`  [ERROR] Falló copia (${task.trip}): ${path.basename(task.src)} -> ${err.message}`);
          })
          .finally(() => {
            active--;
            next();
          });
      }
    }
    next();
  });
}

console.log(`⚙️ Iniciando copia optimizada con concurrencia de ${CONCURRENCY_LIMIT} procesos...`);
processQueue(pendingTasks, CONCURRENCY_LIMIT).then((results) => {
  console.log('\n========================================');
  console.log('🎉 PROCESO DE COPIA FINALIZADO');
  console.log('========================================');
  console.log(`✅ Copiados en esta sesión: ${results.success}`);
  console.log(`❌ Errores en esta sesión: ${results.errors}`);
  console.log('========================================');
  console.log('📊 Resumen final por viaje:');
  
  for (const [trip, stats] of Object.entries(tasksByTrip)) {
    console.log(`   - ${trip}: ${stats.copied} listos | ${stats.failed} fallidos`);
  }
});
