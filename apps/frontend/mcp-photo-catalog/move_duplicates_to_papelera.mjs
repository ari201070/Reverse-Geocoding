import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

const db = new Database('C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db');

// Get all photos
const allPhotos = db.prepare('SELECT id, filename, file_size, file_path, is_duplicate FROM photos').all();

// Get duplicates on F: drive (not in Papelera)
const dupesOnF = allPhotos.filter(p => 
  p.is_duplicate === 1 && 
  p.file_path.startsWith('F:') && 
  !p.file_path.includes('Papelera_Deduplicacion')
);

console.log('=== MOVIENDO DUPLICADOS A PAPELERA ===');
console.log('Total a evaluar:', dupesOnF.length);

let moved = 0;
let skipped = 0;
let errors = 0;
let spaceFreed = 0;

for (const dupe of dupesOnF) {
  // Check if same filename exists elsewhere (not in Papelera)
  const sameNameElsewhere = allPhotos.filter(p => 
    p.id !== dupe.id && 
    p.filename === dupe.filename && 
    !p.file_path.includes('Papelera_Deduplicacion')
  );
  
  // Check if same filename exists in Papelera
  const inPapelera = allPhotos.filter(p => 
    p.filename === dupe.filename && 
    p.file_path.includes('Papelera_Deduplicacion')
  );
  
  if (sameNameElsewhere.length === 0 && inPapelera.length === 0) {
    skipped++;
    continue;
  }
  
  // Build destination path
  const relativePath = dupe.file_path.substring(3); // Remove 'F:'
  const destPath = 'F:\\.Papelera_Deduplicacion' + relativePath;
  const destDir = path.dirname(destPath);
  
  // Check if source exists
  if (!fs.existsSync(dupe.file_path)) {
    skipped++;
    continue;
  }
  
  // Create destination directory
  try {
    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
    }
    
    // Move file
    fs.renameSync(dupe.file_path, destPath);
    moved++;
    spaceFreed += dupe.file_size || 0;
    
    if (moved % 100 === 0) {
      console.log('  Movidas:', moved, '| Espacio:', (spaceFreed / 1024 / 1024).toFixed(0), 'MB');
    }
  } catch (e) {
    errors++;
    if (errors <= 5) {
      console.log('  Error:', e.message);
    }
  }
}

console.log('\n=== RESUMEN ===');
console.log('Movidas:', moved);
console.log('Saltadas (única copia):', skipped);
console.log('Errores:', errors);
console.log('Espacio liberado:', (spaceFreed / 1024 / 1024).toFixed(2), 'MB');

db.close();
