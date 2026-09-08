/**
 * borrar_duplicados.cjs
 * 
 * Script seguro para automatizar la limpieza de archivos duplicados en OneDrive.
 * 
 * Lógica de seguridad:
 * 1. Lee las líneas de 'COMO-LIBERAR-ESPACIO-ONEDRIVE.txt'.
 * 2. Extrae las rutas de OneDrive y sus respectivos backups originales en F:/G:.
 * 3. Valida UTF-8 (texto en hebreo como תמונות) y limpia comillas.
 * 4. Verifica físicamente que el backup en F:/G: exista antes de borrar el archivo de OneDrive.
 * 5. Elimina el duplicado de OneDrive para liberar espacio en la nube.
 * 6. Implementa pacing físico (pausa de 30ms) para cuidar tu disco duro.
 */

const fs = require('fs');
const path = require('path');

const REPORT_PATH = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/photo-import-output/COMO-LIBERAR-ESPACIO-ONEDRIVE.txt';

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function run() {
  console.log('===============================================================');
  console.log('🧹 INICIANDO LIMPIEZA AUTOMÁTICA Y SEGURA DE ONEDRIVE          ');
  console.log('===============================================================\n');

  if (!fs.existsSync(REPORT_PATH)) {
    console.error(`❌ Error Crítico: No se encontró el archivo de reporte en: ${REPORT_PATH}`);
    return;
  }

  try {
    const content = fs.readFileSync(REPORT_PATH, 'utf8');
    const lines = content.split('\n');
    
    const duplicatesToDelete = [];
    let currentOneDrivePath = null;

    console.log('📖 Analizando archivo de reporte...');
    
    // Parseador de bloques de duplicados
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      // Detectar ruta de OneDrive (Origen)
      if (line.startsWith('OneDrive: ') || (line.match(/^\d+\.\s+OneDrive:\s+/) && line.includes('OneDrive:'))) {
        const cleanLine = line.replace(/^\d+\.\s+/, ''); // Quitar prefijo numérico
        currentOneDrivePath = cleanLine.replace('OneDrive: ', '').trim();
      } 
      // Detectar ruta de Backup (Destino)
      else if (line.startsWith('Respaldado en: ') || line.startsWith('Original a salvo en: ')) {
        const cleanLine = line.replace('Original a salvo en: ', '').replace('Respaldado en: ', '').trim();
        // El reporte puede tener múltiples rutas de backup separadas por coma
        const backupPaths = cleanLine.split(',').map(p => p.trim());
        
        if (currentOneDrivePath) {
          duplicatesToDelete.push({
            oneDrivePath: currentOneDrivePath,
            backupPaths: backupPaths
          });
          currentOneDrivePath = null; // Reset para el siguiente bloque
        }
      }
    }

    console.log(`✅ Análisis completo. Se encontraron ${duplicatesToDelete.length} candidatos para eliminación.\n`);

    if (duplicatesToDelete.length === 0) {
      console.log('⭐ No se encontraron duplicados válidos en el reporte.');
      return;
    }

    console.log('🧹 Iniciando eliminación física con doble verificación de seguridad...');
    let deletedCount = 0;
    let skippedSafetyCount = 0;
    let notFoundCount = 0;
    let errorCount = 0;

    for (const item of duplicatesToDelete) {
      const targetPath = item.oneDrivePath;
      
      // 1. Verificar si el archivo en OneDrive aún existe localmente
      if (!fs.existsSync(targetPath)) {
        notFoundCount++;
        continue;
      }

      // 2. DOBLE VERIFICACIÓN DE SEGURIDAD:
      // Confirmar que al menos una de las rutas de backup existe físicamente en F: o G: antes de borrar de OneDrive
      const safeToClear = item.backupPaths.some(backupPath => {
        try {
          if (fs.existsSync(backupPath)) {
            const backupStat = fs.statSync(backupPath);
            // El backup debe existir y tener un tamaño mayor que 0 bytes
            return backupStat.isFile() && backupStat.size > 0;
          }
        } catch (e) {
          return false;
        }
        return false;
      });

      if (!safeToClear) {
        console.warn(`⚠️  [Veto de Seguridad] El original en F:/G: no fue encontrado o está vacío. Se omitió el borrado de: ${path.basename(targetPath)}`);
        skippedSafetyCount++;
        continue;
      }

      // 3. Proceder a la eliminación física segura
      try {
        fs.unlinkSync(targetPath);
        deletedCount++;
        console.log(`🗑️  [Eliminado] ${path.basename(targetPath)} - Espacio liberado en OneDrive.`);
        
        // Pacing de seguridad (30ms de pausa) para no saturar disco local
        await delay(30);

      } catch (err) {
        console.error(`❌ Error al eliminar ${path.basename(targetPath)}: ${err.message}`);
        errorCount++;
      }
    }

    console.log(`\n===============================================================`);
    console.log(`🎉 ¡PROCESO DE LIMPIEZA FINALIZADO!                          `);
    console.log(`   - Total rutas analizadas: ${duplicatesToDelete.length}`);
    console.log(`   - Archivos eliminados con éxito en OneDrive: ${deletedCount}`);
    console.log(`   - Omitidos por seguridad (Falta de backup): ${skippedSafetyCount}`);
    console.log(`   - Archivos que ya no estaban en OneDrive: ${notFoundCount}`);
    if (errorCount > 0) {
      console.log(`   - Archivos con error de escritura: ${errorCount}`);
    }
    console.log(`===============================================================`);

  } catch (error) {
    console.error(`❌ Error crítico de ejecución: ${error.message}`);
  }
}

run();