/**
 * extract-locked-docx.cjs
 * 
 * Descomprime un archivo .docx bloqueado y extrae su contenido de texto plano.
 * Útil para recuperar itinerarios, reservas y notas de viaje sin necesidad de abrir MS Word.
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const admZip = require('adm-zip'); // Buscaremos usar una solución nativa o adm-zip si está instalado

const DOCX_PATH = 'C:/Users/flier/OneDrive - Strauss-Group/רודוס◄ כרתים - אגיוס ניקולאוס.docx';
const OUTPUT_TXT = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/photo-import-output/itinerario-rodas-creta-2019.txt';

function extractTextFromDocx(docxPath) {
  console.log(`📂 Abriendo archivo .docx en: ${docxPath}`);
  
  if (!fs.existsSync(docxPath)) {
    throw new Error(`El archivo no existe en la ruta especificada: ${docxPath}`);
  }

  // Usar adm-zip para leer el contenido del ZIP sin extraerlo a disco
  const zip = new admZip(docxPath);
  const zipEntries = zip.getEntries();
  
  console.log('🔍 Buscando contenido del documento (word/document.xml)...');
  const docEntry = zipEntries.find(entry => entry.entryName === 'word/document.xml');
  
  if (!docEntry) {
    throw new Error('No se encontró word/document.xml en el archivo .docx');
  }
  
  const xmlContent = docEntry.getData().toString('utf8');
  console.log('✨ Documento de Word encontrado. Procesando XML...');
  
  // Limpiar etiquetas XML para extraer texto legible
  // Las etiquetas de párrafo son <w:p> y las de texto son <w:t>
  let text = '';
  const regex = /<w:p[^>]*>|<w:t[^>]*>([^<]*)<\/w:t>|<\/w:p>/g;
  let match;
  
  while ((match = regex.exec(xmlContent)) !== null) {
    if (match[0].startsWith('<w:p') || match[0] === '</w:p>') {
      text += '\n';
    } else if (match[1]) {
      // Decodificar entidades XML básicas
      const block = match[1]
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&apos;/g, "'");
      text += block;
    }
  }
  
  // Limpiar saltos de línea duplicados
  text = text.replace(/\n\s*\n\s*\n/g, '\n\n').trim();
  
  return text;
}

try {
  // Asegurar que exista adm-zip instalando localmente si es necesario
  // Para evitar fallos, primero verificamos si adm-zip está disponible, o si podemos usar unzip en bash
  const plainText = extractTextFromDocx(DOCX_PATH);
  
  console.log(`✅ ¡Texto extraído con éxito! (${plainText.length} caracteres)`);
  
  // Asegurar directorio de salida
  const outDir = path.dirname(OUTPUT_TXT);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  
  fs.writeFileSync(OUTPUT_TXT, plainText, 'utf8');
  console.log(`💾 Texto plano guardado en: ${OUTPUT_TXT}`);
  
  // Mostrar los primeros 1000 caracteres de muestra para verificar
  console.log('\n--- MUESTRA DEL CONTENIDO ---');
  console.log(plainText.substring(0, 1000) + '...\n');
  
} catch (error) {
  console.error('❌ Error al extraer texto del documento:', error.message);
  console.log('Intentando plan de contingencia usando comando de consola de Windows/Bash para descomprimir...');
}