/**
 * Copia final de Chipre con rutas normalizadas (v3 - Node.js)
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';

const REORG_PLAN = './reorganization_plan.csv';
const TARGET_TRIP = 'cyprus';

console.log('═══════════════════════════════════════════════════════════════');
console.log('  FASE 5.1: COPIA FINAL - CHIPRE (RUTAS NORMALIZADAS)');
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

// Filter Cyprus entries
const cyprusLines = lines.filter(l => {
    const parts = parseCSVLine(l);
    return parts[3] === TARGET_TRIP;
});

console.log(`📸 Total archivos Cyprus: ${cyprusLines.length}`);
console.log('');

let total = 0;
let success = 0;
let failed = 0;

for (const line of cyprusLines) {
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
    
    // Get directory and filename
    const srcDir = path.dirname(srcWin);
    const dstDir = path.dirname(dstWin);
    const filename = path.basename(srcWin);
    
    // Create target directory
    if (!fs.existsSync(dstDir)) {
        fs.mkdirSync(dstDir, { recursive: true });
    }
    
    // Copy with robocopy
    try {
        const cmd = `robocopy "${srcDir}" "${dstDir}" "${filename}" /NJH /NJS /NC /NS /NP /MT:8`;
        execSync(cmd, { stdio: 'ignore' });
        success++;
        if (success % 10 === 0) {
            console.log(`  ✅ [${success}/${total}] Copied`);
        }
    } catch (e) {
        failed++;
        console.log(`  ❌ [${total}] Failed: ${path.basename(srcWin)}`);
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
console.log(`   Total archivos: ${total}`);
console.log(`   ✅ Copiados: ${success}`);
console.log(`   ❌ Fallidos: ${failed}`);
console.log(`   ⏱️  Tiempo: ${elapsed} segundos`);
if (elapsed > 0) {
    const speed = (success / elapsed).toFixed(2);
    console.log(`   🚀 Velocidad: ${speed} archivos/segundo`);
}
console.log('');
console.log('✅ Completado.');
