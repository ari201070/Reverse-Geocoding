import fs from 'fs';
import path from 'path';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import http from 'http';
import { URL } from 'url';

const DB_PATH = 'C:\\Users\\flier\\.gemini\\antigravity\\scratch\\photo_catalog.db';
const PORT = 4500;

// 📂 CARPETAS RAÍZ GENERALES
// El script ahora es RECURSIVO: va a escanear todo lo que esté adentro de estas carpetas automáticamente.
const CARPETAS_RAIZ = ['C:\\', 'F:\\', 'G:\\'];

async function lanzarAuditoriaLocal() {
  console.log('🕵️ Iniciando mapa de control de calidad con indexación recursiva...');
  
  // 🧠 Base de datos interna en memoria para búsquedas instantáneas de archivos
  const mapaArchivos = new Map();
  console.log('📦 Escaneando subcarpetas en tu disco F:\\ y C:\\... Por favor, esperá.');

  for (const raiz of CARPETAS_RAIZ) {
    if (!fs.existsSync(raiz)) {
      console.log(`⚠️ La ruta no existe o no está accesible: ${raiz}`);
      continue;
    }
    try {
      // Node v20+ soporta { recursive: true } nativamente. Escanea todo el árbol de carpetas.
      const archivos = fs.readdirSync(raiz, { recursive: true });
      for (const archi of archivos) {
        const rutaCompleta = path.join(raiz, archi);
        try {
          if (fs.statSync(rutaCompleta).isFile()) {
            const nombreBase = path.basename(archi).toLowerCase();
            if (!mapaArchivos.has(nombreBase)) {
              mapaArchivos.set(nombreBase, rutaCompleta);
            }
          }
        } catch (e) {}
      }
    } catch (err) {
      console.log(`⚠️ Error indexando subcarpetas de: ${raiz}. Se usará modo simple.`);
      try {
        const archivos = fs.readdirSync(raiz);
        for (const archi of archivos) {
          const rutaCompleta = path.join(raiz, archi);
          if (fs.statSync(rutaCompleta).isFile()) {
            mapaArchivos.set(archi.toLowerCase(), rutaCompleta);
          }
        }
      } catch (e) {}
    }
  }
  console.log(`✨ ¡Indexación completa! Se encontraron ${mapaArchivos.size} archivos listos para mostrar.\n`);

  const db = await open({
    filename: DB_PATH,
    driver: sqlite3.Database
  });

  const columns = await db.all('PRAGMA table_info(photos)');
  const colNames = columns.map(c => c.name.toLowerCase());
  
  let pathColumn = 'filename';
  if (colNames.includes('path')) pathColumn = 'path';
  else if (colNames.includes('filepath')) pathColumn = 'filepath';

  const query = `
    SELECT 
      ROUND(latitude, 4) as lat, 
      ROUND(longitude, 4) as lng, 
      COALESCE(location_name, 'Sin Nombre Registrado') as location_name,
      COUNT(*) as total_fotos,
      GROUP_CONCAT(filename || ':::' || COALESCE(${pathColumn}, ''), '|||') as archivos
    FROM photos 
    WHERE latitude IS NOT NULL AND latitude != 0 AND longitude IS NOT NULL AND longitude != 0
    GROUP BY ROUND(latitude, 4), ROUND(longitude, 4), COALESCE(location_name, 'Sin Nombre Registrado')
  `;

  const data = await db.all(query);
  await db.close();

  const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <title>QA Map - Diagnóstico de Rutas Inteligente</title>
    <meta charset="utf-8" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; padding: 0; font-family: sans-serif; }
        #map { height: 100vh; width: 100vw; }
        .popup-info { font-size: 13px; line-height: 1.4; width: 340px; }
        .popup-title { font-weight: bold; color: #2c3e50; border-bottom: 2px solid #e74c3c; margin-bottom: 6px; padding-bottom: 3px; }
        .file-box { background: #f8f9fa; border: 1px solid #ddd; padding: 6px; border-radius: 4px; max-height: 250px; overflow-y: auto; margin-top: 5px; }
        .file-item { margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px dashed #ccc; }
        .file-item:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
        .file-name { font-family: monospace; font-weight: bold; color: #2980b9; word-break: break-all; }
        .img-preview { display: block; max-width: 100%; max-height: 140px; margin-top: 4px; border-radius: 4px; border: 1px solid #bbb; background: #fff; object-fit: contain; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map').setView([-34.5968, -58.4093], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        const clusters = ${JSON.stringify(data)};

        clusters.forEach(c => {
            if (c.lat && c.lng) {
                const marker = L.circleMarker([c.lat, c.lng], {
                    radius: c.total_fotos === 1 ? 7 : 12,
                    fillColor: '#e74c3c',
                    color: '#c0392b',
                    weight: 1,
                    fillOpacity: 0.8
                }).addTo(map);

                const listaRaw = c.archivos ? c.archivos.split('|||') : [];
                let htmlArchivos = '<div class="file-box">';
                
                const visibles = listaRaw.slice(0, 4);
                visibles.forEach(item => {
                    const partes = item.split(':::');
                    const name = partes[0];
                    const filepath = partes[1] || name;
                    
                    const urlImagen = \`/ver-foto?path=\${encodeURIComponent(filepath)}&name=\${encodeURIComponent(name)}\`;
                    
                    htmlArchivos += \`<div class="file-item">\` +
                        \`<div class="file-name">📄 \${name}</div>\` +
                        \`<img src="\${urlImagen}" class="img-preview" alt="No encontrada en directorio raíz" />\` +
                        \`</div>\`;
                });

                if (listaRaw.length > 4) {
                    htmlArchivos += \`<div style="color:#7f8c8d; font-size:11px; text-align:center;">... y \${listaRaw.length - 4} más</div>\`;
                }
                htmlArchivos += '</div>';

                marker.bindPopup(
                    \`<div class="popup-info">\` +
                    \`<div class="popup-title">\${c.location_name || 'Punto de Control'}</div>\` +
                    \`<strong>Coords:</strong> \${c.lat}, \${c.lng}<br/>\` +
                    htmlArchivos +
                    \`</div>\`
                );
            }
        });
    </script>
</body>
</html>`;

  const server = http.createServer((req, res) => {
    const parsedUrl = new URL(req.url, `http://localhost:${PORT}`);
    
    if (parsedUrl.pathname === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(htmlContent);
      return;
    }

    if (parsedUrl.pathname === '/ver-foto') {
      const imgPath = parsedUrl.searchParams.get('path');
      const imgName = parsedUrl.searchParams.get('name');
      
      let archivoReal = null;

      // 1. Si llega un path absoluto y existe físicamente, usarlo directamente
      if (imgPath && path.isAbsolute(imgPath) && fs.existsSync(imgPath) && fs.lstatSync(imgPath).isFile()) {
        archivoReal = imgPath;
      }

      // 2. Si no es absoluto, o no existe, usar el mapa de indexación en memoria con el nombre básico
      if (!archivoReal && imgPath) {
        const nombreBasico = path.basename(imgPath).toLowerCase();
        if (mapaArchivos.has(nombreBasico)) {
          archivoReal = mapaArchivos.get(nombreBasico);
        }
      }

      // 3. Fallback secundario con el parámetro name si el anterior no dio resultado
      if (!archivoReal && imgName) {
        const nombreBasicoName = path.basename(imgName).toLowerCase();
        if (mapaArchivos.has(nombreBasicoName)) {
          archivoReal = mapaArchivos.get(nombreBasicoName);
        }
      }

      if (archivoReal) {
        const ext = path.extname(archivoReal).toLowerCase();
        let contentType = 'image/jpeg';
        if (ext === '.png') contentType = 'image/png';
        if (ext === '.heic') contentType = 'image/heic';
        
        res.writeHead(200, { 'Content-Type': contentType });
        fs.createReadStream(archivoReal).pipe(res);
      } else {
        console.log(`\n❌ FOTO NO ENCONTRADA EN NINGUNA SUBCARPETA: Path: "${imgPath}", Name: "${imgName}"`);
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('No localizado');
      }
      return;
    }

    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  });

  server.listen(PORT, () => {
    console.log('\n======================================================');
    console.log(`🚀 SERVIDOR QA ACTIVADO CON INDEXACIÓN TOTAL`);
    console.log(`👉 Entrá a: http://localhost:${PORT}`);
    console.log('======================================================\n');
  });
}

lanzarAuditoriaLocal();