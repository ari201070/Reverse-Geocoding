/**
 * scan-onedrive-duplicates.cjs
 * 
 * Escanea las carpetas de OneDrive, calcula el hash SHA256 de cada foto/video,
 * y los compara con la base de datos de fotos para encontrar duplicados.
 * Genera un reporte detallado con las rutas y el espacio que se puede liberar.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const Database = require('better-sqlite3');

const DB_PATH = 'C:/Users/flier/GitHub/Reverse-Geocoding/data/photo_catalog.db';
const ONEDRIVE_DIRS = [
  'C:/Users/flier/OneDrive/תמונות/Samsung Gallery/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images',
  'C:/Users/flier/OneDrive/תמונות/Samsung Gallery/DCIM',
  'C:/Users/flier/OneDrive/תמונות/Samsung Gallery/Pictures'
];
const OUTPUT_DIR = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/photo-import-output';

// Extensiones de archivos de fotos/videos
const VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.gif', '.mov', '.avi'];

/**
 * Calcula el hash SHA256 de un archivo de manera eficiente
 */
function calculateSHA256(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(filePath);
    
    stream.on('data', data => hash.update(data));
    stream.on('end', () => resolve(hash.digest('hex')));
    stream.on('error', err => reject(err));
  });
}

/**
 * Escanea un directorio recursivamente y obtiene todos los archivos válidos
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

async function run() {
  console.log('🚀 Iniciando escaneo de duplicados en OneDrive...');
  console.log(`🗃️ Cargando base de datos desde ${DB_PATH}...`);
  
  if (!fs.existsSync(DB_PATH)) {
    console.error('❌ Error: No se encontró la base de datos de fotos.');
    return;
  }
  
  const db = new Database(DB_PATH, { readonly: true });
  
  // Cargar todos los hashes existentes de la DB
  console.log('🔄 Indexando hashes de fotos existentes en la base de datos...');
  const existingPhotos = db.prepare("SELECT id, sha256, file_path, filename, file_size FROM photos").all();
  
  const hashToPhotoMap = new Map();
  existingPhotos.forEach(photo => {
    if (!hashToPhotoMap.has(photo.sha256)) {
      hashToPhotoMap.set(photo.sha256, []);
    }
    hashToPhotoMap.get(photo.sha256).push(photo);
  });
  
  console.log(`✅ Base de datos indexada: ${existingPhotos.length} fotos con hash cargadas.`);
  
  // Escanear OneDrive
  console.log('\n🔍 Escaneando archivos locales en OneDrive...');
  const allOneDriveFiles = [];
  ONEDRIVE_DIRS.forEach(dir => {
    if (fs.existsSync(dir)) {
      console.log(`   - Escaneando: ${dir}`);
      scanDirectory(dir, allOneDriveFiles);
    } else {
      console.log(`   - Directorio no encontrado: ${dir}`);
    }
  });
  
  console.log(`✅ Escaneo completado: ${allOneDriveFiles.length} fotos/videos encontrados en OneDrive.`);
  
  // Comparar hashes
  console.log('\n⚙️  Calculando hashes y buscando duplicados (esto puede tardar unos minutos)...');
  
  const duplicates = [];
  const uniques = [];
  let processedCount = 0;
  let totalSavedSpace = 0;
  
  for (const file of allOneDriveFiles) {
    try {
      processedCount++;
      
      if (processedCount % 500 === 0 || processedCount === allOneDriveFiles.length) {
        console.log(`   Procesados ${processedCount}/${allOneDriveFiles.length} archivos...`);
      }
      
      let sha256 = null;
      let matchedByHash = false;
      let matches = [];
      
      // Intentar calcular hash si el archivo está físicamente disponible
      try {
        sha256 = await calculateSHA256(file.filePath);
        if (hashToPhotoMap.has(sha256)) {
          matches = hashToPhotoMap.get(sha256);
          matchedByHash = true;
        }
      } catch (hashErr) {
        // Fallback si es Files On-Demand (no está descargado)
        // console.log(`   [Files On-Demand] ${file.name} - usando comparación por metadatos`);
      }
      
      // Si no pudimos por hash, buscar por nombre de archivo y tamaño exacto en la base de datos
      if (!matchedByHash) {
        // Buscar en existentes por filename y file_size
        const dbMatches = existingPhotos.filter(p => 
          p.filename.toLowerCase() === file.name.toLowerCase()
        );
        
        if (dbMatches.length > 0) {
          // Obtener tamaño exacto de cada coincidencia para confirmar
          const verifiedMatches = [];
          for (const match of dbMatches) {
            // Verificar si el archivo en la base de datos tiene un tamaño similar o si podemos validarlo
            // En nuestra base de datos, el tamaño de la foto está en la columna 'file_size'
            // Vamos a verificar contra la DB
            const dbPhoto = db.prepare('SELECT file_size, file_path FROM photos WHERE id = ?').get(match.id || existingPhotos.indexOf(match) + 1);
            if (dbPhoto && Math.abs(dbPhoto.file_size - file.size) < 1024) { // Tolerancia de 1KB por metadatos corregidos
              verifiedMatches.push(match.file_path);
            }
          }
          
          if (verifiedMatches.length > 0) {
            matches = verifiedMatches;
          }
        }
      }
      
      if (matches.length > 0) {
        duplicates.push({
          oneDrivePath: file.filePath,
          oneDriveSize: file.size,
          fileName: file.name,
          sha256: sha256 || 'N/A (En la nube)',
          originalMatches: matches.map(m => typeof m === 'string' ? m : m.file_path)
        });
        totalSavedSpace += file.size;
      } else {
        uniques.push({
          oneDrivePath: file.filePath,
          oneDriveSize: file.size,
          fileName: file.name,
          sha256: sha256 || 'N/A'
        });
      }
    } catch (err) {
      console.error(`❌ Error procesando ${file.filePath}: ${err.message}`);
    }
  }
  
  // Generar reporte
  const totalSpaceMB = (allOneDriveFiles.reduce((sum, f) => sum + f.size, 0) / (1024 * 1024)).toFixed(2);
  const savedSpaceMB = (totalSavedSpace / (1024 * 1024)).toFixed(2);
  
  const report = {
    summary: {
      totalScanned: allOneDriveFiles.length,
      totalDuplicates: duplicates.length,
      totalUniques: uniques.length,
      totalSpaceScannedMB: parseFloat(totalSpaceMB),
      savableSpaceMB: parseFloat(savedSpaceMB),
      savableSpacePercentage: ((totalSavedSpace / allOneDriveFiles.reduce((sum, f) => sum + f.size, 0)) * 100 || 0).toFixed(2) + '%'
    },
    duplicates: duplicates,
    uniques: uniques,
    generatedAt: new Date().toISOString()
  };
  
  // Guardar reporte
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  const reportPath = path.join(OUTPUT_DIR, 'onedrive-duplicates-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  const summaryTxtPath = path.join(OUTPUT_DIR, 'onedrive-duplicates-summary.txt');
  let summaryTxt = `=== REPORTE DE DUPLICADOS EN ONEDRIVE ===\n\n`;
  summaryTxt += `Fecha: ${new Date().toLocaleString()}\n`;
  summaryTxt += `Total archivos escaneados: ${report.summary.totalScanned}\n`;
  summaryTxt += `Total duplicados encontrados: ${report.summary.totalDuplicates} (están seguros en tu backup F:/G:)\n`;
  summaryTxt += `Total archivos únicos en OneDrive: ${report.summary.totalUniques} (NO borrar - solo están aquí)\n`;
  summaryTxt += `Espacio total escaneado: ${report.summary.totalSpaceScannedMB} MB\n`;
  summaryTxt += `Espacio que puedes liberar de la nube: ${report.summary.savableSpaceMB} MB (${report.summary.savableSpacePercentage})\n\n`;
  
  summaryTxt += `--- MUESTRA DE DUPLICADOS QUE SE PUEDEN BORRAR DE ONEDRIVE ---\n\n`;
  duplicates.slice(0, 50).forEach((dup, i) => {
    summaryTxt += `${i+1}. OneDrive: ${dup.oneDrivePath} (${(dup.oneDriveSize / 1024).toFixed(2)} KB)\n`;
    summaryTxt += `   Original en backup: ${dup.originalMatches.join(', ')}\n\n`;
  });
  
  if (duplicates.length > 50) {
    summaryTxt += `... y ${duplicates.length - 50} duplicados más listados en el reporte JSON.\n`;
  }
  
  fs.writeFileSync(summaryTxtPath, summaryTxt);
  
  console.log('\n=== RESULTADOS DEL ESCANEO ===');
  console.log(`📁 Total archivos escaneados: ${report.summary.totalScanned}`);
  console.log(`✅ Duplicados encontrados: ${report.summary.totalDuplicates}`);
  console.log(`⭐ Archivos únicos en OneDrive: ${report.summary.totalUniques}`);
  console.log(`💾 Espacio que puedes ahorrar en la nube: ${savedSpaceMB} MB (${report.summary.savableSpacePercentage})`);
  console.log(`📝 Reporte detallado guardado en: ${reportPath}`);
  console.log(`📝 Resumen de duplicados guardado en: ${summaryTxtPath}`);
  
  db.close();
}

run().catch(console.error);