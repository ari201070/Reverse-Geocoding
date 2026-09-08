import "dotenv/config";
import fs from "fs";

const ARCHITECT_SYSTEM_PROMPT = `Eres un Ingeniero de Software Senior y Arquitecto de Soluciones GIS especializado en Sistemas de Información Geográfica y optimización de APIs de Geolocalización. Actúas como el "Arquitecto de Reverse Geocoding" para el proyecto "Reverse Geocoding & Consensus Truth Engine".

Tus directivas de arquitectura obligatorias son:
1. Diseño Modular y Desacoplado: Divide tareas complejas en micro-módulos aislados y testeables.
2. Eficiencia de Datos y Soberanía Local (SpatialCache): Prioriza la "Caché Espacial" local y agrupamiento H3 antes de APIs externas.
3. Sinergia de Conocimiento (NotebookLM): Actúa como estratega de alto nivel.
4. Formato de Salida Interoperable: Toda interacción técnica DEBE finalizar con un bloque claro "INSTRUCCIÓN PARA EL AGENTE".

Tono de comunicación: Profesional, estratégico, directo. Responde en Castellano.`;

async function callGeminiAPI(systemPrompt, userPrompt) {
  const apiKey = process.env.GEMINI_API_KEY;
  const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;

  console.log("Consultando al Arquitecto sobre saturación de API...");
  try {
    const response = await fetch(geminiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text: userPrompt }] }],
        systemInstruction: { parts: [{ text: systemPrompt }] },
        generationConfig: { temperature: 0.2, topP: 0.95, topK: 40, maxOutputTokens: 8192 }
      })
    });

    if (response.ok) {
      const result = await response.json();
      if (result.candidates?.[0]?.content?.parts?.[0]?.text) {
        return result.candidates[0].content.parts[0].text;
      }
    }
  } catch (error) {
    console.error("Error Gemini:", error.message);
  }

  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (!openRouterKey) throw new Error("No API key available");

  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${openRouterKey}`,
    },
    body: JSON.stringify({
      model: "google/gemini-2.5-flash:free",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt }
      ],
      temperature: 0.2
    })
  });

  const data = await response.json();
  return data.choices?.[0]?.message?.content || "No response";
}

const userPrompt = `CONSULTA: El agente de programación (AntiGravity) está experimentando constantes bloqueos de cuota y rate-limiting ("gemini está demasiado saturado reintentando en X segundos - intento #Y") al encadenar llamadas y herramientas pesadas. 

Esto destruye el flujo de trabajo continuo. Necesitamos una solución arquitectónica y una estrategia de "Cooldown" y "Pacing" para evitar que el agente sature la API.

¿Cuáles son tus directivas y patrones de diseño específicos para mitigar la saturación de la API de Gemini? 
Por favor, proporciona reglas explícitas de "cooldown" (tiempos de pausa recomendados, reducción de llamadas redundantes, almacenamiento en caché) que el agente deba seguir rígidamente.`;

try {
  const response = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
  console.log("\n====== RESPUESTA DEL ARQUITECTO SOBRE SATURACIÓN ======\n");
  console.log(response);
  console.log("\n======================================================\n");
  fs.writeFileSync("architect-cooldown-response.md", response, "utf8");
} catch (error) {
  console.error("❌ Falló la consulta al Arquitecto:", error.message);
}