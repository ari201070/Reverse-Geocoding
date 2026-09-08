#!/usr/bin/env node
/**
 * copiar_con_powershell.mjs
 * 
 * Copia fotos únicas de OneDrive a F: usando PowerShell para manejar rutas hebreas.
 * Node.js NO puede resolver rutas con caracteres hebreos (תמונות) en Windows.
 * PowerShell SÍ puede.
 * 
 * Flujo:
 * 1. Lee CSV de OneDrive
 * 2. Filtra duplicados (vs photo_catalog.db)
 * 3. Genera script PowerShell que copia archivos
 * 4. Ejecuta PowerShell
 * 5. Registra en SQLite
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const CSV_PATH = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/onedrive-files.csv';
const F_DRIVE_ROOT = 'F:/';
const TEMP_SCRIPT = path.join(__dirname, '..', 'photo-import-output', 'copy-onedrive.ps1');

const MONTH_NAMES_ES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.gif', '.mov', '.avi', '.heic', '.webp'];

function parseOneDriveCSV(csvPath) {
  const content = fs.readFileSync(csvPath, 'utf8');
  const lines = content.split('\n');
  const files = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const matches = line.match(/"([^"]*)"/g);
    if (matches && matches.length >= 4) {
      files.push({
        filePath: matches[0].replace(/"/g, ''),
        name: matches[1].replace(/"/g, ''),
        size: parseInt(matches[2].replace(/"/g, ''), 10),
        attributes: matches[3].replace(/"/g, ''),
      });
    }
  }
  return files;
}

function extractDateFromFilename(fileName) {
  const stdMatch = fileName.match(/(\d{4})(\d{2})(\d{2})[_-]\d{6}/);
  if (stdMatch) return { year: parseInt(stdMatch[1]), month: parseInt(stdMatch[2]) - 1, day: parseInt(stdMatch[3]) };
  const waMatch = fileName.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (waMatch) return { year: parseInt(waMatch[1]), month: parseInt(waMatch[2]) - 1, day: parseInt(waMatch[3]) };
  return null;
}

async function main() {
  console.log('═══════════════════════════════════════════════════');
  console.log('  COPIA DE ONEDRIVE -> F: VIA POWERSHELL');
  console.log('═══════════════════════════════════════════════════\n');

  // 1. Cargar CSV
  const oneDriveFiles = parseOneDriveCSV(CSV_PATH);
  console.log(`📖 Archivos en CSV: ${oneDriveFiles.length}`);

  // 2. Conectar DB y obtener archivos existentes
  const db = new Database(DB_PATH);
  const existingPhotos = db.prepare("SELECT filename, file_size FROM photos").all();
  const existingMap = new Map();
  existingPhotos.forEach(p => {
    const key = p.filename.toLowerCase();
    if (!existingMap.has(key)) existingMap.set(key, []);
    existingMap.get(key).push(p.file_size);
  });
  console.log(`🗄️  Fotos en DB: ${existingPhotos.length}`);

  // 3. Filtrar únicos
  const uniqueFiles = [];
  let dupCount = 0;
  for (const file of oneDriveFiles) {
    const ext = path.extname(file.name).toLowerCase();
    if (!VALID_EXTENSIONS.includes(ext)) continue;
    
    const nameLower = file.name.toLowerCase();
    let isDuplicate = false;
    if (existingMap.has(nameLower)) {
      const sizes = existingMap.get(nameLower);
      isDuplicate = sizes.some(s => Math.abs(s - file.size) < 4096);
    }
    if (isDuplicate) { dupCount++; continue; }
    uniqueFiles.push(file);
  }
  console.log(`\n📊 Duplicados: ${dupCount} | Únicos para copiar: ${uniqueFiles.length}`);

  if (uniqueFiles.length === 0) {
    console.log('✅ No hay archivos nuevos para copiar.');
    db.close();
    return;
  }

  // 4. Generar script PowerShell
  const outputDir = path.dirname(TEMP_SCRIPT);
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

  let psScript = '# Auto-generado por copiar_con_powershell.mjs\n';
  psScript += '$ErrorActionPreference = "Continue"\n';
  psScript += '$copied = 0\n';
  psScript += '$failed = 0\n';
  psScript += '$skipped = 0\n\n';

  // Mapeo para registrar en SQLite después
  const fileMapping = [];

  for (const file of uniqueFiles) {
    const dateInfo = extractDateFromFilename(file.name);
    let destDir;
    
    if (dateInfo) {
      const year = dateInfo.year;
      const monthName = MONTH_NAMES_ES[dateInfo.month];
      destDir = `${F_DRIVE_ROOT}${year}\\${monthName}`;
    } else {
      destDir = `${F_DRIVE_ROOT}SinFecha`;
    }

    const srcPath = file.filePath.replace(/\\/g, '\\\\');
    const destPath = `${destDir}\\${file.name}`.replace(/\\/g, '\\\\');
    const destPathForward = `${destDir}/${file.name}`;

    // PowerShell script to copy with verification
    psScript += `try {\n`;
    psScript += `  $src = '${srcPath}'\n`;
    psScript += `  $dst = '${destPath}'\n`;
    psScript += `  if (!(Test-Path $dst)) {\n`;
    psScript += `    $destDir = Split-Path $dst -Parent\n`;
    psScript += `    if (!(Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }\n`;
    psScript += `    Copy-Item -LiteralPath $src -Destination $dst -Force\n`;
    psScript += `    $copied++\n`;
    psScript += `  } else {\n`;
    psScript += `    $skipped++\n`;
    psScript += `  }\n`;
    psScript += `} catch {\n`;
    psScript += `  Write-Host "ERROR: $($_.Exception.Message) - ${file.name}"\n`;
    psScript += `  $failed++\n`;
    psScript += `}\n`;

    fileMapping.push({
      src: file.filePath,
      dest: destPathForward,
      name: file.name,
      size: file.size,
      year: dateInfo?.year || null,
      month: dateInfo ? dateInfo.month + 1 : null,
    });
  }

  psScript += `\nWrite-Host ""\n`;
  psScript += `Write-Host "========================================"\n`;
  psScript += `Write-Host "  RESULTADO DE COPIA"\n`;
  psScript += `Write-Host "========================================"\n`;
  psScript += `Write-Host "  Copiados:  $copied"\n`;
  psScript += `Write-Host "  Fallidos:  $failed"\n`;
  psScript += `Write-Host "  Saltados:  $skipped"\n`;
  psScript += `Write-Host "========================================"\n`;

  // PowerShell requires BOM to read UTF-8 Hebrew characters correctly
  const BOM = '\uFEFF';
  fs.writeFileSync(TEMP_SCRIPT, BOM + psScript, 'utf8');
  console.log(`\n📝 Script PowerShell generado: ${TEMP_SCRIPT}`);
  console.log(`   Total operaciones: ${uniqueFiles.length}`);

  // 5. Ejecutar PowerShell
  console.log('\n⚡ Ejecutando copia via PowerShell...\n');
  try {
    const result = execSync(
      `powershell -NoProfile -ExecutionPolicy Bypass -File "${TEMP_SCRIPT}"`,
      { encoding: 'utf8', timeout: 600000, stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, MSYS_NO_PATHCONV: '1' } }
    );
    console.log(result);
  } catch (err) {
    console.error('❌ Error en PowerShell:', err.message);
    if (err.stdout) console.log(err.stdout);
    if (err.stderr) console.error(err.stderr);
  }

  // 6. Registrar en SQLite (solo los que existen en F:)
  console.log('\n🗄️  Registrando archivos copiados en photo_catalog.db...');
  const insertStmt = db.prepare(`
    INSERT OR IGNORE INTO photos (file_path, folder_source, filename, file_size, file_ext, date_source)
    VALUES (?, ?, ?, ?, ?, 'onedrive_backup')
  `);

  let registeredCount = 0;
  const checkExists = db.prepare("SELECT id FROM photos WHERE file_path = ? LIMIT 1");

  for (const file of fileMapping) {
    // Verificar que el archivo existe en destino
    try {
      const destCheck = execSync(
        `powershell -NoProfile -Command "Test-Path -LiteralPath '${file.dest.replace(/'/g, "''")}'"`,
        { encoding: 'utf8', timeout: 5000, env: { ...process.env, MSYS_NO_PATHCONV: '1' } }
      ).trim();

      if (destCheck === 'True') {
        const existing = checkExists.get(file.dest);
        if (!existing) {
          insertStmt.run(file.dest, path.dirname(file.dest), file.name, file.size, path.extname(file.name));
          registeredCount++;
        }
      }
    } catch (e) {
      // Skip verification errors
    }
  }

  console.log(`✅ Registrados en DB: ${registeredCount}`);
  db.close();

  console.log('\n═══════════════════════════════════════════════════');
  console.log('  PROCESO COMPLETADO');
  console.log('═══════════════════════════════════════════════════');
}

main().catch(err => {
  console.error('❌ Error fatal:', err);
  process.exit(1);
});
