#!/usr/bin/env node
/**
 * Consulta al Arquitecto de Reverse Geocoding sobre el script de importación de fotos
 * Ejecuta: node consult-architect-import.cjs
 */

import "dotenv/config";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const ARCHITECT_SYSTEM_PROMPT = `Eres un Ingeniero de Software Senior y Arquitecto de Soluciones GIS especializado en Sistemas de Información Geográfica y optimización de APIs de Geolocalización. Actúas como el "Arquitecto de Reverse Geocoding" para el proyecto "Reverse Geocoding & Consensus Truth Engine".

Tus directivas de arquitectura obligatorias son:
1. Diseño Modular y Desacoplado: Divide tareas complejas en micro-módulos aislados y testeables.
2. Eficiencia de Datos y Soberanía Local (SpatialCache): Prioriza la "Caché Espacial" local y agrupamiento de coordenadas por índices hexagonales H3 (Resolución 9) antes de llamar a APIs externas pagadas.
3. Sinergia de Conocimiento (NotebookLM): Actúa como estratega de alto nivel. Para documentación profunda, delega o indica consultar la "Fuente de Verdad" (NotebookLM) vía MCP.
4. Formato de Salida Interoperable: Toda interacción técnica DEBE finalizar con un bloque "INSTRUCCIÓN PARA EL AGENTE" que el agente pueda ejecutar directamente.

Tono: Profesional, estratégico, directo. Responde en Castellano.`;

// Read the import script
const importScript = fs.readFileSync(
  path.join(__dirname, "import-photos-as-trips.cjs"),
  "utf8"
);

// Read the architect proposal for context
const architectProposal = fs.readFileSync(
  "C:/Users/flier/.gemini/antigravity/scratch/Reverse-Geocoding/architect_proposal.md",
  "utf8"
);

const userPrompt = `CONSULTA OBLIGATORIA AL ARQUITECTO - Proyecto Travel-Booking-Document-Hub

CONTEXTO:
El usuario flier tiene un proyecto "Travel-Booking-Document-Hub" que gestiona documentos de viaje (vuelos, hoteles, reservas) desde Google Drive con IA. Tiene un MCP server "photo-catalog" con 34,037 fotos geolocalizadas en photo_catalog.db.

Se creó un script de importación (import-photos-as-trips.cjs) que:
1. Lee fotos de photo_catalog.db (SQLite)
2. Normaliza países (Hebrew→English, Italian→English, etc.)
3. Agrupa por país + año
4. Fusiona países consecutivos dentro de una ventana de 7 días en un solo "viaje"
5. Genera una "actividad" por día por país
6. Exporta JSON para importar al localStorage de la app (travel_bookings)

CÓDIGO DEL SCRIPT (resumen ejecutivo):
- Lee 5,590 fotos con fecha + país (de 34,037 totales)
- Crea 18 viajes (2008-2026): Israel, Croacia, Montenegro, Argentina, Grecia, Eslovenia, Italia, Bosnia
- Genera 101 actividades
- Normalización de países: COUNTRY_NORMALIZATION map + CITY_TO_COUNTRY fallback
- Merge window: 7 días entre países para considerar "mismo viaje"

PROBLEMA ACTUAL:
El script agrupa por país+año pero NO considera:
- Distancia geográfica real entre países (Israel→Croacia vs Israel→Argentina)
- Fechas exactas de reservas de vuelos/hoteles (que ya tenemos en la app)
- La lógica de "Consensus Truth Engine" del proyecto Reverse-Geocoding

PREGUNTAS AL ARQUITECTO:
1. ¿Cómo deberíamos mejorar la lógica de agrupación de fotos en viajes usando H3 y la Caché Espacial?
2. ¿Deberíamos integrar el script de importación con el MCP photo-catalog existente, o mantenerlo como script aislado?
3. ¿Cómo aplicaríamos el "Algoritmo de Consenso y Prudencia Agéntica" (Antigravity 2.0) para validar que una foto pertenece a un viaje específico?
4. ¿Qué mejoras arquitectónicas recomiendas para el script actual?

Proporciona un diseño modular con "INSTRUCCIÓN PARA EL AGENTE" al final.`;

async function callGeminiAPI(systemPrompt, userPrompt) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error("GEMINI_API_KEY no configurada en .env");
  }
  const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;

  console.error("🤖 Consultando al Arquitecto de Reverse Geocoding...");
  
  const response = await fetch(geminiUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: userPrompt }] }],
      systemInstruction: { parts: [{ text: systemPrompt }] },
      generationConfig: { temperature: 0.2, topP: 0.95, topK: 40, maxOutputTokens: 8192 }
    })
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Gemini API error ${response.status}: ${errText}`);
  }

  const result = await response.json();
  if (result.candidates?.[0]?.content?.parts?.[0]?.text) {
    return result.candidates[0].content.parts[0].text;
  }
  
  throw new Error("Respuesta vacía de Gemini API");
}

async function main() {
  try {
    const response = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
    
    console.log("\n====== RESPUESTA DEL ARQUITECTO ======\n");
    console.log(response);
    console.log("\n======================================\n");
    
    // Save to file
    const outputPath = path.join(__dirname, "architect-import-response.md");
    fs.writeFileSync(outputPath, response, "utf8");
    console.log(`✅ Respuesta guardada en: ${outputPath}`);
    
  } catch (error) {
    console.error("❌ Falló la consulta:", error.message);
    process.exit(1);
  }
}

main();