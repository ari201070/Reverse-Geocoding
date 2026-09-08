const fs = require('fs');

const txtPath = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/photo-import-output/COMO-LIBERAR-ESPACIO-ONEDRIVE.txt';

if (!fs.existsSync(txtPath)) {
  console.log('❌ No se encontró el archivo de reporte.');
  process.exit(1);
}

const content = fs.readFileSync(txtPath, 'utf8').replace(/^\uFEFF/, '');
const lines = content.split(/\r?\n/);

let borrados = 0;
let noEncontrados = 0;

lines.forEach(line => {
  let file = line.trim().replace(/^["']|["']$/g, '');
  if (!file) return;

  if (fs.existsSync(file)) {
    try {
      fs.unlinkSync(file);
      borrados++;
    } catch (e) {
      console.log(`Error eliminando: ${file}`);
    }
  } else {
    noEncontrados++;
  }
});

console.log('----------------------------------------');
console.log(`🎉 ¡PROCESO COMPLETADO!`);
console.log(`✅ Fotos borradas de tu disco: ${borrados}`);
console.log(`⚠️ No encontradas o ya borradas: ${noEncontrados}`);
console.log('----------------------------------------');
