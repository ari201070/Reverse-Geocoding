const fs = require('fs');
const path = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/photo-import-output/COMO-LIBERAR-ESPACIO-ONEDRIVE.txt';

if (!fs.existsSync(path)) {
  console.log('❌ No se encontró el archivo TXT.');
  process.exit(1);
}

const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);
let borrados = 0;
let intentados = 0;

lines.forEach((line) => {
  // Extraer la ruta de Windows ignorando comillas, números o texto alrededor
  const match = line.match(/([A-Za-z]:\\[^"\r\n]+|[A-Za-z]:\/[^"\r\n]+)/);
  if (match) {
    let file = match[1].replace(/["']/g, '').trim();
    intentados++;
    
    if (fs.existsSync(file)) {
      try {
        fs.unlinkSync(file);
        borrados++;
      } catch (e) {
        console.error(`⚠️ Error al borrar ${file}: ${e.message}`);
      }
    } else if (intentados <= 3) {
      console.log(`🔍 [Muestra de prueba] No detectado en disco: ${file}`);
    }
  }
});

console.log(`\n📊 Líneas de ruta detectadas en el TXT: ${intentados}`);
console.log(`🎉 ¡Listo! Se borraron ${borrados} archivos duplicados de OneDrive.`);
