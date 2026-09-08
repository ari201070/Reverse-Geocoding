import fs from 'fs';
import path from 'path';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import { GoogleGenAI } from '@google/genai';

// ⚙️ Configuración del entorno y Base de Datos
const DB_PATH = 'C:\\Users\\flier\\.gemini\\antigravity\\scratch\\photo_catalog.db';
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

// Función auxiliar para pausar la ejecución
const esperar = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function aplicarCorrecciones() {
  console.log('🔄 Iniciando script de curaduría y corrección espacial...');
  
  // 1. Conectar a la base de datos local
  const db = await open({
    filename: DB_PATH,
    driver: sqlite3.Database
  });

  // 2. Traer las fotos atrapadas bajo el "Falso Positivo" del Obelisco
  // Buscamos las coordenadas por defecto (-34.603... o -34.59...) que asignó el importador
  const fotosSospechosas = await db.all(`
    SELECT id, filename, location_name, latitude, longitude 
    FROM photos 
    WHERE latitude LIKE '-34.60%' 
       OR latitude LIKE '-34.59%'
  `);

  console.log(`📊 Se detectaron ${fotosSospechosas.length} fotos en la zona default de Buenos Aires.`);

  let corregidas = 0;
  let saltadas = 0;

  // 3. Recorrer el lote con freno de mano para evitar el Rate Limit
  for (const foto of fotosSospechosas) {
    const nombreMinuscula = foto.filename.toLowerCase();

    // Filtro inteligente: Si el nombre dice explícitamente Palermo, Recoleta o Buenos Aires, asumimos que está bien
    if (nombreMinuscula.includes('palermo') || nombreMinuscula.includes('recoleta') || nombreMinuscula.includes('buenos aires')) {
      saltadas++;
      continue;
    }

    console.log(`\n🔎 Analizando archivo: "${foto.filename}"`);
    console.log(`   Ubicación actual errónea: ${foto.location_name}`);

    try {
      // Consultamos a Gemini usando el modelo flash estable
      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: `Analizá el siguiente nombre de archivo de una foto y deducí su ubicación geográfica real en Argentina (coordenadas aproximadas y nombre del lugar/región).
        
Archivo: "${foto.filename}"

Si el archivo contiene referencias claras a lugares específicos fuera de Buenos Aires (como "Cueva de las Manos", "Bariloche", "Mendoza", "Rosario", etc.), deducí las coordenadas correctas de ese punto turístico o ciudad. Si el nombre no da ninguna pista geográfica real, respondé con "NO_INFO".

Tu respuesta debe ser ESTRICTAMENTE un objeto JSON con el siguiente formato plano (sin bloques de código markdown, sin texto extra, solo el JSON):
{
  "status": "CORRECTED",
  "latitude": -47.156,
  "longitude": -70.654,
  "location_name": "Cueva de las Manos, Santa Cruz"
}
o si no hay pistas:
{
  "status": "NO_INFO"
}`,
      });

      // Limpiamos la respuesta por si el modelo ignora la regla del markdown
      const textoLimpio = response.text.trim().replace(/```json|```/g, '');
      const resultado = JSON.parse(textoLimpio);

      if (resultado.status === 'CORRECTED' && resultado.latitude && resultado.longitude) {
        // 4. Inyección transaccional en la DB de las coordenadas reales
        await db.run(
          `UPDATE photos 
           SET latitude = ?, longitude = ?, location_name = ? 
           WHERE id = ?`,
          [resultado.latitude, resultado.longitude, resultado.location_name, foto.id]
        );
        console.log(`🎯 ¡Corregida! -> Nueva ubicación: ${resultado.location_name} [${resultado.latitude}, ${resultado.longitude}]`);
        corregidas++;
      } else {
        console.log(`⚠️ Gemini no encontró pistas suficientes para mover este archivo.`);
      }

    } catch (error) {
      console.error(`❌ Error procesando ${foto.filename}:`, error.message);
      
      // Salvavidas: Si golpeamos el Rate Limit estricto, dormimos el script un rato más largo
      if (error.message.includes('429') || error.message.includes('quota')) {
        console.log('⏳ [API SATURADA] Pausando ejecución por 15 segundos para liberar cuota...');
        await esperar(15000);
      }
    }

    // 🔥 EL THROTTLE CLAVE: Pausa obligatoria de 2 segundos entre bucles para cuidar los RPM
    console.log(`⏱️ Respetando límite de velocidad. Esperando 2 segundos...`);
    await esperar(2000);
  }

  await db.close();
  console.log(`\n🏁 Curaduría finalizada.`);
  console.log(`📊 Resumen: Analizadas: ${fotosSospechosas.length} | Corregidas: ${corregidas} | Confirmadas en BA: ${saltadas}`);
}

aplicarCorrecciones();