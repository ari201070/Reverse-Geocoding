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

// Filtrar viajes a procesar (SOLO Sin_Viaje)
const targetLines = dataLines.filter(l => {
  const parts = parseCSVLine(l);
  const trip = parts[3];
  return trip === 'Sin_Viaje';
});

console.log(`📋 Total de archivos en categoría 'Sin_Viaje': ${targetLines.length} archivos.`);

// 2. Preparar tareas
let pendingTasks = [];
let completadosYa = 0;
let faltantesOrigen = 0;

console.log('🔍 Validando estado actual en disco (skip-first)...');

for (let i = 0; i < targetLines.length; i++) {
  const parts = parseCSVLine(targetLines[i]);
  const src = parts[1];
  const dst = parts[2];
  const trip = parts[3];

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
    // El destino no existe, lo copiamos
  }

  if (dstSize === srcSize) {
    completadosYa++;
  } else {
    pendingTasks.push({ src, dst });
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
            // Reportamos cada 200 archivos
            if (success % 200 === 0 || success === tasks.length) {
              console.log(`  ➡️ Progreso: ${success}/${tasks.length} copiados...`);
            }
          })
          .catch(err => {
            errors++;
            console.error(`  [ERROR] Falló copia: ${path.basename(task.src)} -> ${err.message}`);
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

console.log(`⚙️ Iniciando copia masiva de Sin_Viaje con concurrencia de ${CONCURRENCY_LIMIT} procesos...`);
const startTime = Date.now();
processQueue(pendingTasks, CONCURRENCY_LIMIT).then((results) => {
  const endTime = Date.now();
  const timeSecs = ((endTime - startTime) / 1000).toFixed(1);
  const timeMins = (timeSecs / 60).toFixed(2);
  
  console.log('\n========================================');
  console.log('🎉 PROCESO DE COPIA Sin_Viaje FINALIZADO');
  console.log('========================================');
  console.log(`⏱️ Tiempo de ejecución: ${timeMins} minutos (${timeSecs}s)`);
  console.log(`✅ Copiados en esta sesión: ${results.success}`);
  console.log(`❌ Errores en esta sesión: ${results.errors}`);
  console.log(`⏭️ Ya existían en destino: ${completadosYa}`);
  console.log(`🔴 Faltantes en origen (Papelera/etc): ${faltantesOrigen}`);
  console.log('========================================');
});
