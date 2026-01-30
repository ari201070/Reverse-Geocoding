// Prueba de cálculo de distancia con las coordenadas reales

const userPhoto = { lat: -28.545981, lon: -57.195382 };

const cities = {
    'corrientes': { lat: -27.4692, lon: -58.8306 },
    'ibera': { lat: -28.5167, lon: -57.1833 }
};

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radio de la Tierra en km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

console.log('=== PRUEBA DE DETECCIÓN DE CIUDAD ===\n');
console.log('Coordenadas de la foto:', userPhoto);
console.log('\nDistancias calculadas:');

for (const [name, coords] of Object.entries(cities)) {
    const distance = calculateDistance(
        userPhoto.lat, userPhoto.lon,
        coords.lat, coords.lon
    );
    console.log(`  ${name}: ${distance.toFixed(2)} km`);
}

// Encontrar la más cercana
let closestCity = null;
let minDistance = Infinity;

for (const [name, coords] of Object.entries(cities)) {
    const distance = calculateDistance(
        userPhoto.lat, userPhoto.lon,
        coords.lat, coords.lon
    );
    if (distance < minDistance) {
        minDistance = distance;
        closestCity = name;
    }
}

console.log(`\n✅ RESULTADO: "${closestCity}" (${minDistance.toFixed(2)} km)`);
console.log(`Radio de detección: 200 km`);
console.log(`¿Dentro del rango? ${minDistance < 200 ? 'SÍ' : 'NO'}`);
