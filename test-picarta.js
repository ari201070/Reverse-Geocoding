// test-picarta.js
// Script simple para probar el proxy de Picarta AI localmente (con vercel dev)
// Requiere que .env tenga VITE_PICARTA_API_TOKEN

import fetch from 'node-fetch'; // Podría no ser necesario en Node 18+ pero asegura compatibilidad
import dotenv from 'dotenv';
dotenv.config();

const testImageBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="; // Una imagen 1x1 base64 válida (aunque no útil para geolocalización)

async function testPicarta() {
    console.log("🚀 Probando integración Picarta AI via Proxy...");
    
    try {
        const response = await fetch("http://localhost:3000/api/picarta", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image_base64: testImageBase64 })
        });

        const data = await response.json();
        
        if (response.ok) {
            console.log("✅ Conexión existosa al proxy.");
            console.log("Respuesta de la IA:", data);
        } else {
            console.error("❌ Error en el proxy:", data);
        }
    } catch (err) {
        console.error("❌ Error de red (¿está corriendo 'vercel dev'?):", err.message);
    }
}

testPicarta();
