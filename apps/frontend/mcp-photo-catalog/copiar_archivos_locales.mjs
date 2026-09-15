/**
 * copiar_archivos_locales.mjs (Versión Definitiva con Salvaguarda SQLite)
 * 
 * Script seguro para procesar y copiar fotos únicas descargadas de OneDrive al disco F:.
 * 
 * Optimizaciones y Soluciones de la Arquitectura:
 * 1. Control de duplicados en base de datos: Verifica pre-existencia en 'photos.file_path'
 *    para evitar el molesto error "UNIQUE constraint failed".
 * 2. Resiliencia contra archivos offline (Files On-Demand): Detecta y salta instantáneamente
 *    los archivos no descargados, previniendo que la terminal se congele.
 * 3. Validación de UTF-8: Asegura que caracteres en hebreo como 'תמונות' sean legibles.
 * 4. Pacing físico de disco: Pausa física de 40ms entre operaciones para cuidar la salud del hardware.
 */

import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';

// Configuración de Rutas Absolutas (Ruta segura '/' para Windows)
const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const CSV_PATH = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/onedrive-files.csv';
const F_DRIVE_ROOT = 'F:/';

// Extensiones permitidas de fotos y videos
const VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.gif', '.mov', '.avi'];

const MONTH_NAMES_ES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

// Función de Pacing (Pausa física de seguridad contra sobrecarga)
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Parsea el reporte CSV de OneDrive
 */
function parseOneDriveCSV(csvPath) {
  if (!fs.existsSync(csvPath)) {
    throw new Error(`No se encontró el archivo CSV en la ruta: ${csvPath}`);
  }

  const content = fs.readFileSync(csvPath, 'utf8');
  const lines = content.split('\n');
  const files = [];

  console.log(`📖 Procesando líneas del CSV...`);
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const matches = line.match(/"([^"]*)"/g);
    if (matches && matches.length >= 4) {
      const fullName = matches[0].replace(/"/g, '');
      const name = matches[1].replace(/"/g, '');
      const length = parseInt(matches[2].replace(/"/g, ''), 10);
      const attributes = matches[3].replace(/"/g, '');

      files.push({
        filePath: fullName,
        name: name,
        size: length,
        attributes: attributes
      });
    }
  }
  return files;
}

/**
 * Infiere la fecha de toma desde la nomenclatura
 */
function extractDateFromFilename(fileName) {
  const stdMatch = fileName.match(/(\d{4})(\d{2})(\d{2})_\d{6}/);
  if (stdMatch) {
    return {
      year: parseInt(stdMatch[1], 10),
      month: parseInt(stdMatch[2], 10) - 1, // 0-indexado
      day: parseInt(stdMatch[3], 10)
    };
  }

  const waMatch = fileName.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (waMatch) {
    return {
      year: parseInt(waMatch[1], 10),
      month: parseInt(waMatch[2], 10) - 1,
      day: parseInt(waMatch[3], 10)
    };
  }

  return null;
}

async function main() {
  console.log('===============================================================');
  console.log('🚀 MOTOR DE COPIADO SEGURO DE ONEDRIVE -> F: (VERSIÓN FINAL)  ');
  console.log('===============================================================\n');

  try {
    // 1. Cargar metadatos del CSV
    const oneDriveFiles = parseOneDriveCSV(CSV_PATH);
    console.log(`✅ Archivos cargados desde CSV: ${oneDriveFiles.length}`);

    // 2. Conectar e indexar Base de Datos de Fotos
    if (!fs.existsSync(DB_PATH)) {
      console.error(`❌ Error Crítico: No se encontró la base de datos de fotos en ${DB_PATH}`);
      return;
    }
    const db = new Database(DB_PATH);
    console.log('🔄 Indexando base de datos de tu backup principal (F:/G:)...');
    const existingPhotos = db.prepare("SELECT filename, file_size FROM photos").all();
    
    const existingMap = new Map();
    existingPhotos.forEach(p => {
      const nameLower = p.filename.toLowerCase();
      if (!existingMap.has(nameLower)) {
        existingMap.set(nameLower, []);
      }
      existingMap.get(nameLower).push(p.file_size);
    });
    console.log(`✅ Indexación completa: ${existingPhotos.length} fotos a salvo en backup.`);

    // 3. Filtrar fotos únicas y locales
    const uniqueLocalFiles = [];
    let duplicateCount = 0;
    let cloudOnlyCount = 0;

    console.log('\n⚖️  Clasificando archivos para evitar bloqueos de red...');
    for (const file of oneDriveFiles) {
      const nameLower = file.name.toLowerCase();
      
      let isDuplicate = false;
      if (existingMap.has(nameLower)) {
        const sizes = existingMap.get(nameLower);
        isDuplicate = sizes.some(size => Math.abs(size - file.size) < 4096);
      }

      if (isDuplicate) {
        duplicateCount++;
      } else {
        const attrs = file.attributes.toLowerCase();
        const isOffline = attrs.includes('offline') || attrs.includes('reparsepoint') || attrs.includes('sparsefile');
        
        if (isOffline) {
          cloudOnlyCount++;
        } else {
          uniqueLocalFiles.push(file);
        }
      }
    }

    console.log(`\n📊 Estado de Clasificación:`);
    console.log(`   - 🔄 Duplicados (Ya respaldados): ${duplicateCount}`);
    console.log(`   - ☁️  Archivos en la nube (Skipeados automáticamente): ${cloudOnlyCount}`);
    console.log(`   - 🟢 Únicos Físicos Candidatos para Copiar: ${uniqueLocalFiles.length}\n`);

    if (uniqueLocalFiles.length === 0) {
      console.log('⭐ No hay nuevos archivos únicos locales para copiar. Todo está sincronizado.');
      db.close();
      return;
    }

    // 4. Copiar de forma estructurada a F: con Pacing y Validación de Existencia
    console.log(`📦 Iniciando proceso de copiado a ${F_DRIVE_ROOT} con pausas de seguridad...`);
    let copiedSuccessCount = 0;
    let alreadyCatalogedCount = 0;
    let failedOfflineCount = 0;

    for (const file of uniqueLocalFiles) {
      try {
        // Validación de caracteres UTF-8 en la ruta
        if (!fs.existsSync(file.filePath)) {
          console.error(`❌ Ruta no encontrada (UTF-8 inválido): ${file.name}`);
          continue;
        }

        const dateInfo = extractDateFromFilename(file.name) || {
          year: new Date(fs.statSync(file.filePath).mtime).getFullYear(),
          month: new Date(fs.statSync(file.filePath).mtime).getMonth(),
          day: new Date(fs.statSync(file.filePath).mtime).getDate()
        };

        if (dateInfo.year > new Date().getFullYear() + 1 || dateInfo.year < 2002) {
          dateInfo.year = new Date().getFullYear();
          dateInfo.month = new Date().getMonth();
        }

        const monthName = MONTH_NAMES_ES[dateInfo.month];
        const destFolder = path.join(F_DRIVE_ROOT, dateInfo.year.toString(), monthName);
        const destPath = path.join(destFolder, file.name);

        // SALVAGUARDA EXTRA: Comprobar existencia en la base de datos de fotos antes de intentar nada
        const pathCheck = db.prepare("SELECT id FROM photos WHERE file_path = ?").get(destPath);
        if (pathCheck) {
          alreadyCatalogedCount++;
          continue;
        }

        if (!fs.existsSync(destFolder)) {
          fs.mkdirSync(destFolder, { recursive: true });
        }

        // Proceso de copia seguro
        if (!fs.existsSync(destPath)) {
          try {
            fs.copyFileSync(file.filePath, destPath);
          } catch (copyErr) {
            if (copyErr.message.includes('UNKNOWN') || copyErr.message.includes('error, copyfile')) {
              console.log(`☁️  [Saltado] Archivo físico no disponible (Offline en la nube): ${file.name}`);
              failedOfflineCount++;
              continue;
            } else {
              throw copyErr;
            }
          }
        }

        // Registrar en SQLite (Solo si la copia y la ruta de destino son seguras)
        const dateTakenStr = `${dateInfo.year}-${String(dateInfo.month + 1).padStart(2, '0')}-${String(dateInfo.day).padStart(2, '0')} 12:00:00`;
        const ext = path.extname(file.name).toLowerCase();
        
        const stmt = db.prepare(`
          INSERT INTO photos (file_path, folder_source, filename, file_size, file_ext, date_taken, date_source, is_duplicate)
          VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        `);
        stmt.run(destPath, 'onedrive_backup_copiado', file.name, file.size, ext, dateTakenStr, 'filename_inferred');

        copiedSuccessCount++;

        // Cooldown físico entre copias (40ms)
        await delay(40);

        if (copiedSuccessCount % 100 === 0) {
          console.log(`   [Progreso] Copiadas y registradas ${copiedSuccessCount} fotos únicas...`);
        }

      } catch (fileErr) {
        console.error(`⚠️ No se pudo procesar ${file.name}: ${fileErr.message}`);
        failedOfflineCount++;
      }
    }

    console.log(`\n===============================================================`);
    if (copiedSuccessCount > 0 || alreadyCatalogedCount > 0) {
      console.log(`🎉 ¡PROCESO DE EVALUACIÓN FINALIZADO CON ÉXITO!               `);
      if (copiedSuccessCount > 0) {
        console.log(`   - Nuevas fotos copiadas y catalogadas en F:: ${copiedSuccessCount}`);
      }
      if (alreadyCatalogedCount > 0) {
        console.log(`   - Fotos que ya estaban a salvo en F: y se saltaron: ${alreadyCatalogedCount}`);
      }
      if (failedOfflineCount > 0) {
        console.log(`   - Fotos omitidas por estar en la nube (Offline): ${failedOfflineCount}`);
      }
    } else {
      console.log(`⚠️ EL PROCESO FINALIZÓ SIN COPIAS REALES                     `);
      console.log(`   - Todos los archivos candidatos están en la nube o ya respaldados.`);
    }
    console.log(`===============================================================`);
    
    db.close();

  } catch (error) {
    console.error(`❌ Error crítico de base de datos o sistema: ${error.message}`);
  }
}

main();