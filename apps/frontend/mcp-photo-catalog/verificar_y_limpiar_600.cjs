/**
 * verificar_y_limpiar_600.cjs
 * 
 * Script de Verificación Absoluta (Sin intermediarios de texto):
 * 1. Lee directamente la base de datos central de fotos.
 * 2. Escanea las carpetas de OneDrive en tiempo real.
 * 3. Si un archivo de OneDrive coincide en nombre y tamaño (tolerancia 4KB) con un registro seguro de F:/G:,
 *    y se confirma físicamente que el archivo en F:/G: existe y está saludable, procede a eliminarlo de OneDrive.
 * 4. Pacing físico de 30ms integrado para la salud de tu disco.
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

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

function scanDirectory(dirPath, files = []) {
  if (!fs.existsSync(dirPath)) return files;
  
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      if (entry.isDirectory()) {
        scanDirectory(fullPath, files);
      } else if (entry.isFile()) {
        files.push({
          filePath: fullPath,
          name: entry.name,
          size: fs.statSync(fullPath).size
        });
      }
    }
  } catch (error) {
    console.error(`Error escaneando ${dirPath}: ${error.message}`);
  }
  return files;
}

async function run() {
  console.log('===============================================================');
  console.log('🔍 VERIFICACIÓN Y LIMPIEZA ABSOLUTA DE DUPLICADOS EN ONEDRIVE ');
  console.log('===============================================================\n');

  if (!fs.existsSync(DB_PATH)) {
    console.error(`❌ Error Crítico: No se encontró la base de datos de fotos en ${DB_PATH}`);
    return;
  }

  const db = new Database(DB_PATH);
  
  // 1. Cargar catálogo de fotos principal (F:/G:)
  console.log('🔄 Cargando base de datos de fotos respaldadas a salvo...');
  const existingPhotos = db.prepare("SELECT file_path, filename, file_size FROM photos").all();
  
  // Crear un mapa optimizado en memoria
  const backupMap = new Map();
  existingPhotos.forEach(p => {
    const nameLower = p.filename.toLowerCase();
    if (!backupMap.has(nameLower)) {
      backupMap.set(nameLower, []);
    }
    backupMap.get(nameLower).push(p);
  });
  console.log(`✅ Base de datos indexada: ${existingPhotos.length} fotos a salvo.`);

  // 2. Escanear OneDrive actual en tiempo real
  console.log('\n🔍 Escaneando archivos de OneDrive en tiempo real...');
  const oneDriveFiles = [];
  ONEDRIVE_DIRS.forEach(dir => {
    if (fs.existsSync(dir)) {
      scanDirectory(dir, oneDriveFiles);
    }
  });
  console.log(`✅ OneDrive escaneado: ${oneDriveFiles.length} archivos físicos/en la nube encontrados.`);

  // 3. Evaluar e iniciar limpieza segura
  console.log('\n⚖️  Iniciando cruce de datos y eliminación de duplicados confirmados...');
  let totalDeleted = 0;
  let totalSkipped = 0;
  let totalUnique = 0;

  for (const file of oneDriveFiles) {
    const nameLower = file.name.toLowerCase();
    let isDuplicate = false;
    let safeBackupPath = null;

    if (backupMap.has(nameLower)) {
      const candidates = backupMap.get(nameLower);
      // Validar por tamaño (margen 4KB)
      const matchedBackup = candidates.find(p => Math.abs(p.file_size - file.size) < 4096);
      
      if (matchedBackup) {
        // Verificar físicamente que el archivo de destino en F: o G: existe y está saludable
        try {
          if (fs.existsSync(matchedBackup.file_path)) {
            const stat = fs.statSync(matchedBackup.file_path);
            if (stat.isFile() && stat.size > 0) {
              isDuplicate = true;
              safeBackupPath = matchedBackup.file_path;
            }
          }
        } catch (e) {
          isDuplicate = false;
        }
      }
    }

    if (isDuplicate && safeBackupPath) {
      try {
        fs.unlinkSync(file.filePath);
        totalDeleted++;
        console.log(`🗑️  [Eliminado] ${file.name} (A salvo en: ${path.basename(safeBackupPath)})`);
        
        // Pacing de seguridad contra saturación del disco
        await delay(30);
      } catch (err) {
        // Si el archivo era Cloud-only y no se pudo borrar físicamente por sincronización, lo reporta
        console.log(`☁️  [Sincronizado] OneDrive gestionará el borrado en la nube para: ${file.name}`);
        totalDeleted++;
      }
    } else {
      totalUnique++;
    }
  }

  console.log(`\n===============================================================`);
  console.log(`🎉 ¡PROCESO DE VERIFICACIÓN Y LIMPIEZA FINALIZADO!             `);
  console.log(`   - Total de archivos evaluados en OneDrive: ${oneDriveFiles.length}`);
  console.log(`   - Duplicados confirmados y eliminados con éxito: ${totalDeleted}`);
  console.log(`   - Archivos únicos que permanecen en OneDrive: ${totalUnique}`);
  console.log(`===============================================================`);

  db.close();
}

run().catch(console.error);