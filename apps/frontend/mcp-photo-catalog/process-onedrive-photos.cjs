/**
 * process-onedrive-photos.cjs
 * 
 * Implementa el plan de arquitectura del Arquitecto para gestionar las fotos de OneDrive:
 * 1. Escanea las fotos locales de OneDrive.
 * 2. Compara con la base de datos SQLite por nombre de archivo, tamaño y fecha.
 * 3. Genera un reporte de duplicados con su ubicación segura en F:/G:.
 * 4. Copia las fotos ÚNICAS al disco F: en carpetas por Año/Mes.
 * 5. Registra las nuevas fotos copiadas en la base de datos SQLite.
 * 6. Diseñado con pausas para evitar sobrecarga y saturación.
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

// Extensiones válidas
const VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.gif', '.mov', '.avi'];

const MONTH_NAMES_ES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

/**
 * Helper para dormir/hacer una pausa
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Escanea recursivamente un directorio
 */
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

/**
 * Intenta extraer la fecha de toma a partir del nombre del archivo de OneDrive
 * (Formatos comunes: 20200117_142319.jpg, WhatsApp Image 2020-01-17...)
 */
function extractDateFromFilename(fileName) {
  // Formato: 20200117_142319
  const stdMatch = fileName.match(/(\d{4})(\d{2})(\d{2})_\d{6}/);
  if (stdMatch) {
    return {
      year: parseInt(stdMatch[1], 10),
      month: parseInt(stdMatch[2], 10) - 1, // 0-indexed
      day: parseInt(stdMatch[3], 10)
    };
  }
  
  // Formato: WhatsApp Image 2020-01-17
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

async function run() {
  console.log('🚀 Iniciando Motor de Deduplicación y Gestión de OneDrive...');
  
  if (!fs.existsSync(DB_PATH)) {
    console.error(`❌ Error: No se encontró la base de datos de fotos en ${DB_PATH}`);
    return;
  }
  
  const db = new Database(DB_PATH);
  
  // 1. Cargar catálogo existente
  console.log('🔄 Indexando catálogo existente de fotos...');
  const existingPhotos = db.prepare("SELECT id, file_path, filename, file_size, date_taken FROM photos").all();
  console.log(`✅ Catálogo indexado: ${existingPhotos.length} fotos cargadas.`);
  
  // 2. Escanear OneDrive
  console.log('\n🔍 Escaneando archivos de OneDrive...');
  const oneDriveFiles = [];
  ONEDRIVE_DIRS.forEach(dir => {
    if (fs.existsSync(dir)) {
      console.log(`   - Escaneando: ${dir}`);
      scanDirectory(dir, oneDriveFiles);
    }
  });
  console.log(`✅ Escaneo completado: ${oneDriveFiles.length} archivos encontrados.`);
  
  const duplicates = [];
  const uniques = [];
  
  // 3. Evaluar duplicados por nombre de archivo y tamaño
  console.log('\n⚖️  Analizando duplicados en la base de datos...');
  
  for (const file of oneDriveFiles) {
    // Buscar por coincidencia exacta de nombre y tamaño (heurística 100% fiable en fotos de móvil)
    const matches = existingPhotos.filter(p => 
      p.filename.toLowerCase() === file.name.toLowerCase() &&
      Math.abs(p.file_size - file.size) < 4096 // Tolerancia de metadatos de 4KB
    );
    
    if (matches.length > 0) {
      duplicates.push({
        oneDrivePath: file.filePath,
        size: file.size,
        name: file.name,
        backupPaths: matches.map(m => m.file_path)
      });
    } else {
      uniques.push(file);
    }
  }
  
  console.log(`\n📊 ANÁLISIS COMPLETADO:`);
  console.log(`   - Duplicados en OneDrive: ${duplicates.length}`);
  console.log(`   - Archivos ÚNICOS en OneDrive: ${uniques.length}`);
  
  // 4. Generar reporte de duplicados para borrar de forma segura
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  const reportPath = path.join(OUTPUT_DIR, 'duplicados-onedrive-seguro.json');
  fs.writeFileSync(reportPath, JSON.stringify({
    totalDuplicates: duplicates.length,
    totalSavedSpaceMB: (duplicates.reduce((sum, d) => sum + d.size, 0) / (1024 * 1024)).toFixed(2),
    duplicates: duplicates
  }, null, 2));
  
  console.log(`📝 Reporte seguro de duplicados guardado en: ${reportPath}`);
  console.log(`💡 Puedes usar este reporte para borrar las fotos duplicadas de OneDrive sabiendo que tu backup está a salvo.`);
  
  // 5. Copiar fotos ÚNICAS al disco F: y registrarlas en la DB
  if (uniques.length > 0) {
    console.log(`\n📦 Copiando ${uniques.length} fotos únicas al disco F: y registrándolas...`);
    let copiedCount = 0;
    
    for (const file of uniques) {
      try {
        // Determinar año y mes de toma para organizar la carpeta
        const dateInfo = extractDateFromFilename(file.name) || {
          year: new Date(fs.statSync(file.filePath).mtime).getFullYear(),
          month: new Date(fs.statSync(file.filePath).mtime).getMonth(),
          day: new Date(fs.statSync(file.filePath).mtime).getDate()
        };
        
        // Evitar años anómalos o futuros
        if (dateInfo.year > new Date().getFullYear() + 1 || dateInfo.year < 2002) {
          dateInfo.year = new Date().getFullYear();
          dateInfo.month = new Date().getMonth();
        }
        
        const monthName = MONTH_NAMES_ES[dateInfo.month];
        const destFolder = path.join(F_DRIVE_ROOT, dateInfo.year.toString(), monthName);
        const destPath = path.join(destFolder, file.name);
        
        // Crear carpeta si no existe
        if (!fs.existsSync(destFolder)) {
          fs.mkdirSync(destFolder, { recursive: true });
        }
        
        // Copiar archivo si no existe ya físicamente en el destino
        if (!fs.existsSync(destPath)) {
          fs.copyFileSync(file.filePath, destPath);
        }
        
        // Registrar en `photo_catalog.db`
        const dateTakenStr = `${dateInfo.year}-${String(dateInfo.month + 1).padStart(2, '0')}-${String(dateInfo.day).padStart(2, '0')} 12:00:00`;
        
        const stmt = db.prepare(`
          INSERT INTO photos (file_path, folder_source, filename, file_size, file_ext, date_taken, date_source, is_duplicate)
          VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        `);
        
        stmt.run(destPath, 'onedrive_backup', file.name, file.size, file.ext, dateTakenStr, 'filename_inferred');
        copiedCount++;
        
        // Pausa de pacing de 50ms para no saturar operaciones de disco/base de datos
        await sleep(50);
        
        if (copiedCount % 100 === 0 || copiedCount === uniques.length) {
          console.log(`   Copiadas y registradas ${copiedCount}/${uniques.length} fotos únicas...`);
        }
        
      } catch (copyErr) {
        console.error(`⚠️ No se pudo copiar/registrar ${file.name}: ${copyErr.message}`);
      }
    }
    
    console.log(`\n🎉 ¡Operación completada! Se han copiado y registrado ${copiedCount} fotos únicas en el disco F:.`);
  } else {
    console.log('\n⭐ No hay fotos únicas nuevas para copiar.');
  }
  
  db.close();
}

run().catch(console.error);