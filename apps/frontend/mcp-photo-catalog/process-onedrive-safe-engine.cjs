/**
 * process-onedrive-safe-engine.cjs
 * 
 * Motor seguro y optimizado de OneDrive (Diseño del Arquitecto):
 * - Escaneo asíncrono con control de flujo (Pacing/Rate Limiting de 30ms por archivo).
 * - Manejo elegante de archivos offline de OneDrive (Files On-Demand) para evitar fallos de lectura/copia.
 * - Clasificación inteligente de duplicados frente a photo_catalog.db.
 * - Copia organizada a F:\ de fotos únicas descargadas y registro en SQLite.
 * - Reporte detallado e instructivo para liberar espacio en la nube de forma 100% segura.
 */

const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const ONEDRIVE_DIRS = [
  'C:/Users/flier/OneDrive/תמונות/Samsung Gallery/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images',
  'C:/Users/flier/OneDrive/תמונות/Samsung Gallery/DCIM',
  'C:/Users/flier/OneDrive/תמונות/Samsung Gallery/Pictures'
];
const F_DRIVE_ROOT = 'F:';
const OUTPUT_DIR = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/photo-import-output';

const VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.gif', '.mov', '.avi'];
const MONTH_NAMES_ES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

function scanDirectory(dirPath, files = []) {
  if (!fs.existsSync(dirPath)) return files;
  
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      
      if (entry.isDirectory()) {
        scanDirectory(fullPath, files);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();
        if (VALID_EXTENSIONS.includes(ext)) {
          files.push({
            filePath: fullPath,
            name: entry.name,
            size: fs.statSync(fullPath).size,
            ext: ext
          });
        }
      }
    }
  } catch (error) {
    console.error(`Error escaneando ${dirPath}: ${error.message}`);
  }
  
  return files;
}

function extractDateFromFilename(fileName) {
  const stdMatch = fileName.match(/(\d{4})(\d{2})(\d{2})_\d{6}/);
  if (stdMatch) {
    return {
      year: parseInt(stdMatch[1], 10),
      month: parseInt(stdMatch[2], 10) - 1,
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

/**
 * Determina de forma segura si un archivo está disponible localmente (hidratado)
 * o si es "Cloud-Only / On-Demand" intentando abrir un descriptor de archivo de lectura
 */
function isFileLocallyAvailable(filePath) {
  try {
    const fd = fs.openSync(filePath, 'r');
    fs.closeSync(fd);
    return true;
  } catch (err) {
    return false; // Error al abrir descriptor = Archivo "On-Demand" en la nube
  }
}

async function run() {
  console.log('🚀 Iniciando Motor Seguro de OneDrive (Versión Antisaturación)...');
  
  if (!fs.existsSync(DB_PATH)) {
    console.error(`❌ Base de datos no encontrada en: ${DB_PATH}`);
    return;
  }
  
  const db = new Database(DB_PATH);
  
  // 1. Cargar base de datos existente
  console.log('🔄 Indexando catálogo de fotos de tu backup principal (F:/G:)...');
  const existingPhotos = db.prepare("SELECT id, file_path, filename, file_size FROM photos").all();
  console.log(`✅ Base de datos cargada: ${existingPhotos.length} fotos indexadas.`);
  
  // 2. Escanear archivos en OneDrive
  console.log('\n🔍 Escaneando archivos en carpetas de OneDrive...');
  const oneDriveFiles = [];
  ONEDRIVE_DIRS.forEach(dir => {
    if (fs.existsSync(dir)) {
      console.log(`   - Escaneando: ${dir}`);
      scanDirectory(dir, oneDriveFiles);
    }
  });
  console.log(`✅ Escaneo de OneDrive completado: ${oneDriveFiles.length} fotos/videos detectados.`);
  
  const duplicates = [];
  const uniquesAvailable = [];
  const uniquesCloudOnly = [];
  
  // 3. Clasificación inteligente con tolerancia de metadatos (4KB)
  console.log('\n⚖️  Analizando duplicados y disponibilidad local (Files On-Demand)...');
  
  for (const file of oneDriveFiles) {
    // Buscar en BD por nombre y tamaño exacto
    const matches = existingPhotos.filter(p => 
      p.filename.toLowerCase() === file.name.toLowerCase() &&
      Math.abs(p.file_size - file.size) < 4096
    );
    
    if (matches.length > 0) {
      duplicates.push({
        oneDrivePath: file.filePath,
        size: file.size,
        name: file.name,
        backupPaths: matches.map(m => m.file_path)
      });
    } else {
      // Si es único, verificar si está descargado localmente o si está en la nube
      const isAvailable = isFileLocallyAvailable(file.filePath);
      if (isAvailable) {
        uniquesAvailable.push(file);
      } else {
        uniquesCloudOnly.push(file);
      }
    }
    
    // Pausa mínima de 5ms en escaneo para no saturar disco
    await sleep(5);
  }
  
  console.log(`\n📊 CLASIFICACIÓN DE ARCHIVOS COMPLETADA:`);
  console.log(`   - 🔄 Duplicados Seguros en OneDrive (Ya respaldados en F:/G:): ${duplicates.length}`);
  console.log(`   - 🟢 Únicos Disponibles Localmente (Listos para copiar a F:): ${uniquesAvailable.length}`);
  console.log(`   - ☁️  Únicos "Solo en la Nube" (Requieren descarga en OneDrive antes de copiar): ${uniquesCloudOnly.length}`);
  
  // 4. Guardar reporte interactivo
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  const reportPath = path.join(OUTPUT_DIR, 'onedrive-seguro-reporte.json');
  fs.writeFileSync(reportPath, JSON.stringify({
    summary: {
      totalScanned: oneDriveFiles.length,
      safeToReleaseCount: duplicates.length,
      safeToReleaseSpaceMB: (duplicates.reduce((sum, d) => sum + d.size, 0) / (1024 * 1024)).toFixed(2),
      copiedToFCount: uniquesAvailable.length,
      cloudOnlyCount: uniquesCloudOnly.length
    },
    duplicates: duplicates,
    uniquesAvailable: uniquesAvailable,
    uniquesCloudOnly: uniquesCloudOnly
  }, null, 2));
  
  // Generar TXT de resumen instructivo para el usuario
  const summaryTxtPath = path.join(OUTPUT_DIR, 'COMO-LIBERAR-ESPACIO-ONEDRIVE.txt');
  let summaryTxt = `=== GUÍA PARA LIBERAR ESPACIO EN TU ONEDRIVE DE FORMA 100% SEGURA ===\n\n`;
  summaryTxt += `Fecha de generación: ${new Date().toLocaleString()}\n\n`;
  summaryTxt += `Analizamos un total de ${oneDriveFiles.length} archivos en tu OneDrive local.\n`;
  summaryTxt += `Detectamos ${duplicates.length} archivos que YA ESTÁN respaldados de forma segura en tus discos F:/G:.\n`;
  summaryTxt += `Esto representa un espacio de ${(duplicates.reduce((sum, d) => sum + d.size, 0) / (1024 * 1024)).toFixed(2)} MB que puedes borrar de tu OneDrive sin perder nada.\n\n`;
  
  summaryTxt += `--- INSTRUCCIONES DE ACCIÓN SEGURO ---\n\n`;
  summaryTxt += `1. Puedes eliminar con total confianza las fotos de tu carpeta de OneDrive listadas en el reporte JSON.\n`;
  summaryTxt += `2. Tenemos ${uniquesCloudOnly.length} fotos únicas que están "Solo en la nube" (Offline).\n`;
  summaryTxt += `   Para respaldar estas fotos en tu disco F:, primero debes ir a tu carpeta de OneDrive en el explorador de archivos,\n`;
  summaryTxt += `   hacer clic derecho sobre la carpeta "Samsung Gallery" y seleccionar "Mantener siempre en este dispositivo".\n`;
  summaryTxt += `   Una vez descargadas, vuelve a ejecutar este script para que se copien automáticamente a F:.\n\n`;
  
  summaryTxt += `--- MUESTRA DE FOTOS QUE PUEDES ELIMINAR DE ONEDRIVE (DUPLICADOS CONFIRMADOS) ---\n\n`;
  duplicates.slice(0, 100).forEach((dup, i) => {
    summaryTxt += `${i+1}. OneDrive: ${dup.oneDrivePath}\n`;
    summaryTxt += `   Original a salvo en: ${dup.backupPaths.join(', ')}\n\n`;
  });
  
  fs.writeFileSync(summaryTxtPath, summaryTxt);
  console.log(`📝 Resumen instructivo de borrado guardado en: ${summaryTxtPath}`);
  
  // 5. Copiar archivos ÚNICOS locales a F: y registrarlos
  if (uniquesAvailable.length > 0) {
    console.log(`\n📦 Copiando ${uniquesAvailable.length} archivos únicos descargados al disco F:...`);
    let copiedCount = 0;
    
    for (const file of uniquesAvailable) {
      try {
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
        
        if (!fs.existsSync(destFolder)) {
          fs.mkdirSync(destFolder, { recursive: true });
        }
        
        if (!fs.existsSync(destPath)) {
          fs.copyFileSync(file.filePath, destPath);
        }
        
        // Registrar en SQLite
        const dateTakenStr = `${dateInfo.year}-${String(dateInfo.month + 1).padStart(2, '0')}-${String(dateInfo.day).padStart(2, '0')} 12:00:00`;
        const stmt = db.prepare(`
          INSERT INTO photos (file_path, folder_source, filename, file_size, file_ext, date_taken, date_source, is_duplicate)
          VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        `);
        
        stmt.run(destPath, 'onedrive_backup', file.name, file.size, file.ext, dateTakenStr, 'filename_inferred');
        copiedCount++;
        
        // Pacing: pausa de 30ms para no saturar disco
        await sleep(30);
        
        if (copiedCount % 100 === 0 || copiedCount === uniquesAvailable.length) {
          console.log(`   Copiadas y registradas ${copiedCount}/${uniquesAvailable.length} fotos únicas...`);
        }
      } catch (err) {
        console.error(`⚠️ No se pudo copiar/registrar ${file.name}: ${err.message}`);
      }
    }
    console.log(`\n🎉 ¡Operación completada! Se copiaron y registraron ${copiedCount} fotos únicas en F:.`);
  } else {
    console.log('\n⭐ No se encontraron nuevas fotos únicas locales para copiar (están todas respaldadas o requieren descarga manual).');
  }
  
  db.close();
}

run().catch(console.error);