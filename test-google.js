import fetch from 'node-fetch';

async function testGoogle() {
    console.log("--- Testing Google Places API (Level 3) ---");
    const GOOGLE_KEY = 'AIzaSyD182OZ7oW1WYe5-TzoJaM2wHyglq6-YIU';
    const obelisco = { latitude: -34.6037, longitude: -58.3816 };
    
    try {
        const res = await fetch('https://places.googleapis.com/v1/places:searchNearby', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': GOOGLE_KEY,
                'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress'
            },
            body: JSON.stringify({
                locationRestriction: {
                    circle: { center: obelisco, radius: 500 }
                },
                maxResultCount: 1
            })
        });

        const data = await res.json();
        console.log("Google Response:", JSON.stringify(data, null, 2));
    } catch (e) {
        console.error("Google test failed:", e.message);
    }
}

testGoogle();
