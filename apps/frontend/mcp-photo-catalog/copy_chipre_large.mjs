/**
 * Copia final de Chipre - Fase 2: Archivos grandes (>10MB)
 */

import fs from 'fs';
import path from 'path';

const REORG_PLAN = './reorganization_plan.csv';
const TARGET_TRIP = 'cyprus';
const MIN_SIZE = 10 * 1024 * 1024; // 10MB

console.log('═══════════════════════════════════════════════════════════════');
console.log('  FASE 5.2: COPIA CHIPRE - ARCHIVOS GRANDES (>10MB)');
console.log('═══════════════════════════════════════════════════════════════');
console.log('');

const startTime = Date.now();

// Read and parse CSV properly
const csvContent = fs.readFileSync(REORG_PLAN, 'utf8');
const lines = csvContent.split('\n').filter(l => l.trim());

// Parse CSV line by line
function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            result.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    result.push(current);
    return result;
}

// Filter Cyprus entries with large files
const cyprusLines = lines.filter(l => {
    const parts = parseCSVLine(l);
    return parts[3] === TARGET_TRIP;
});

const largeFiles = cyprusLines.filter(l => {
    const parts = parseCSVLine(l);
    const src = parts[1];
    if (!fs.existsSync(src)) return false;
    const stats = fs.statSync(src);
    return stats.size > MIN_SIZE;
});

console.log(`📸 Total archivos grandes: ${largeFiles.length}`);
console.log('');

let total = 0;
let success = 0;
let failed = 0;

for (const line of largeFiles) {
    total++;
    const parts = parseCSVLine(line);
    const srcWin = parts[1];
    const dstWin = parts[2];
    
    // Check source exists
    if (!fs.existsSync(srcWin)) {
        console.log(`  ❌ [${total}] Not found: ${path.basename(srcWin)}`);
        failed++;
        continue;
    }
    
    const stats = fs.statSync(srcWin);
    const sizeMB = (stats.size / 1024 / 1024).toFixed(1);
    
    // Create target directory
    const dstDir = path.dirname(dstWin);
    if (!fs.existsSync(dstDir)) {
        fs.mkdirSync(dstDir, { recursive: true });
    }
    
    // Copy with Node.js
    try {
        console.log(`  📁 [${total}/${largeFiles.length}] Copiando ${path.basename(srcWin)} (${sizeMB} MB)...`);
        fs.copyFileSync(srcWin, dstWin);
        success++;
        console.log(`  ✅ Completado`);
    } catch (e) {
        failed++;
        console.log(`  ❌ Failed: ${e.message}`);
    }
}

const endTime = Date.now();
const elapsed = Math.floor((endTime - startTime) / 1000);

console.log('');
console.log('═══════════════════════════════════════════════════════════════');
console.log('  REPORTE FINAL');
console.log('═══════════════════════════════════════════════════════════════');
console.log('');
console.log('📊 RESUMEN:');
console.log(`   Total archivos grandes: ${total}`);
console.log(`   ✅ Copiados: ${success}`);
console.log(`   ❌ Fallidos: ${failed}`);
console.log(`   ⏱️  Tiempo: ${elapsed} segundos`);
if (elapsed > 0) {
    const speed = (success / elapsed).toFixed(2);
    console.log(`   🚀 Velocidad: ${speed} archivos/segundo`);
}
console.log('');
console.log('✅ Completado. Todas las fotos de Chipre copiadas.');
