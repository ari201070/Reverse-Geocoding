// .data/download_geojson.js
import fs from 'fs';
import https from 'https';
import path from 'path';

const url = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson';
const targetDir = path.join(process.cwd(), '.data');
const targetFile = path.join(targetDir, 'world_countries.geojson');

if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
}

console.log(`[INFO] Iniciando descarga de GeoJSON desde: ${url}`);
console.log(`[INFO] Destino: ${targetFile}`);

const file = fs.createWriteStream(targetFile);

https.get(url, (response) => {
    if (response.statusCode !== 200) {
        console.error(`[ERROR] Error al descargar: Código de estado ${response.statusCode}`);
        file.close();
        fs.unlinkSync(targetFile);
        process.exit(1);
    }

    response.pipe(file);

    file.on('finish', () => {
        file.close();
        const stats = fs.statSync(targetFile);
        console.log(`[OK] Descarga completa. Archivo guardado con éxito.`);
        console.log(`[OK] Tamaño del archivo: ${(stats.size / 1024).toFixed(2)} KB`);
        process.exit(0);
    });
}).on('error', (err) => {
    fs.unlink(targetFile, () => {});
    console.error(`[ERROR] Fallo en la descarga: ${err.message}`);
    process.exit(1);
});
