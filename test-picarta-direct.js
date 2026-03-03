// test-picarta-direct.js
// Validación directa del token para evitar dependencia de vercel dev
import fetch from 'node-fetch';
import dotenv from 'dotenv';
dotenv.config();

const token = process.env.VITE_PICARTA_API_TOKEN;
const testImageBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

async function test() {
    console.log(`🔍 Probando token: ${token}`);
    try {
        const res = await fetch("https://picarta.ai/classify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ TOKEN: token, IMAGE: testImageBase64, TOP_K: 1 })
        });
        const data = await res.json();
        console.log("Status:", res.status);
        console.log("Respuesta:", data);
    } catch (e) {
        console.error("Error:", e.message);
    }
}
test();
