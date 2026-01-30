
const https = require('https');

const API_KEY = 'AIzaSyBMI6e0c93cqhyUyqZQB_Y0Rqo3UpAZ9Rw';

// Coordenadas de prueba
const TEST_CASES = [
    { name: 'VIP Rosario', lat: -32.9493526, lng: -60.6300769 }, // VIP Rosario (Rioja y Alejo Rossell)
    { name: 'Esteros del Iberá', lat: -28.539824, lng: -57.147255 }
];

function testGeocoding(name, lat, lng) {
    const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${API_KEY}&language=es`;
    
    console.log(`\n--- Probando: ${name} ---`);
    console.log(`URL: ${url.replace(API_KEY, 'HIDDEN_KEY')}`); // Ocultar key en logs por seguridad

    https.get(url, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
            try {
                const json = JSON.parse(data);
                if (json.status !== 'OK') {
                    console.error('❌ ERROR API:', json.status, json.error_message || '');
                    return;
                }

                // Lógica idéntica a photoMetadata.ts
                const results = json.results;
                const poi = results.find(r => 
                    r.types.includes('point_of_interest') || 
                    r.types.includes('establishment')
                );

                if (poi) {
                    console.log('✅ DETECTADO (POI):', poi.name || poi.formatted_address);
                    console.log('   Tipos:', poi.types.join(', '));
                } else {
                    console.log('⚠️ Sin POI específico. Dirección:', results[0].formatted_address);
                }
            } catch (e) {
                console.error('❌ Error parseando JSON:', e.message);
            }
        });
    }).on('error', (e) => {
        console.error('❌ Error de red:', e.message);
    });
}

console.log('Iniciando prueba de geocodificación aislada...');
TEST_CASES.forEach(test => testGeocoding(test.name, test.lat, test.lng));
