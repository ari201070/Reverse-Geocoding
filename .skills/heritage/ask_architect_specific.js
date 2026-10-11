import "dotenv/config";
import fs from "fs";

const ARCHITECT_SYSTEM_PROMPT = `Eres un Ingeniero de Software Senior y Arquitecto de Soluciones GIS especializado en Sistemas de Información Geográfica y optimización de APIs de Geolocalización. Actúas como el "Arquitecto de Reverse Geocoding" para el proyecto "Reverse Geocoding & Consensus Truth Engine".

Tus directivas de arquitectura obligatorias son:
1. Diseño Modular y Desacoplado: Divide tareas complejas en micro-módulos aislados y testeables.
2. Eficiencia de Datos y Soberanía Local (SpatialCache): Prioriza la Caché Espacial y celdas H3 (Resolución 9) antes de llamar a APIs externas.
3. Sinergia de Conocimiento (NotebookLM): Actúa como estratega de alto nivel.
4. Formato de Salida Interoperable: Toda interacción técnica DEBE finalizar con "INSTRUCCIÓN PARA EL AGENTE" si requiere acción.

Tono de comunicación: Profesional, estratégico, enfocado en optimización de rendimiento y OPEX, y directo. Responde en Castellano.`;

async function callGeminiAPI(systemPrompt, userPrompt) {
  const apiKey = process.env.GEMINI_API_KEY || "AIzaSyA81InS4O_wKnFGmKAUg-2DL63UXyyQEKs";
  const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;

  console.log("Intentando llamar a Gemini API nativa...");
  try {
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

    if (response.ok) {
      const result = await response.json();
      if (result.candidates?.[0]?.content?.parts?.[0]?.text) {
        console.log("✅ Conexión exitosa con la API de Gemini nativa.");
        return result.candidates[0].content.parts[0].text;
      }
    } else {
      console.log(`⚠️ Gemini API nativa retornó estado ${response.status}. Iniciando failover...`);
    }
  } catch (error) {
    console.log(`⚠️ Error Gemini nativo: ${error.message}. Iniciando failover...`);
  }

  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (!openRouterKey) {
    throw new Error("Ambos métodos fallaron: Gemini API nativa dio error y OPENROUTER_API_KEY no está configurada.");
  }

  console.log("Intentando llamar a través de OpenRouter...");
  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${openRouterKey}`,
      "HTTP-Referer": "https://localhost:3000",
      "X-Title": "Reverse Geocoding Architect Bridge"
    },
    body: JSON.stringify({
      model: "liquid/lfm-2.5-1.2b-instruct:free",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt }
      ],
      temperature: 0.2
    })
  });

  if (response.ok) {
    const data = await response.json();
    if (data.choices?.[0]?.message?.content) {
      console.log("✅ Conexión exitosa con OpenRouter.");
      return data.choices[0].message.content;
    }
  }
  throw new Error("Fallo crítico en APIs.");
}

async function askArchitect() {
  const query = `El usuario flier me consulta sobre la lógica (si es que la hay) de la resolución de un lote de fotos tomadas el 2/10/2025 en Rosario, Santa Fe. El itinerario y sus resoluciones en la UI según las imágenes son:
- 13:32:41 -> 20251002_133241.jpg -> Facultad de Ciencias Económicas y Estadística - UNR
- 13:33:17 -> 20251002_133317.jpg -> Estadio Marcelo Bielsa (¡Misma coordenada GPS o muy cercana!)
- 13:33:25 -> 20251002_133325.jpg -> Estadio Marcelo Bielsa
- 13:34:20 -> 20251002_133420.jpg -> Estadio Marcelo Bielsa
- 13:35:55 -> 20251002_133555.jpg -> Foto 20251002_133555.jpg_... (Sin coordenadas GPS, pero clasificado en el cluster 'Facultad de Ciencias Económicas y Estadística - UNR' con confianza del 50% requiriendo validación manual)
- 13:37:21 -> 20251002_133721.jpg -> Facultad de Ciencias Económicas y Estadística - UNR
- 13:37:46 -> 20251002_133746.jpg -> Facultad de Ciencias Económicas y Estadística - UNR

¿Cómo es posible que con las mismas coordenadas (u otras muy cercanas) y en un lapso de menos de 5 minutos, el geocodificador resuelva algunas fotos como la Facultad de Ciencias Económicas y Estadística - UNR y otras como el Estadio Marcelo Bielsa, y que la foto sin GPS a las 13:35:55 quede asociada al clúster de la Facultad de Ciencias Económicas?
Explícame detalladamente la lógica de desambiguación espacial, temporal, herencia por proximidad, indexación H3 y la influencia del OCR/Landmarks en esta clasificación.`;

  const context = "El usuario flier quiere entender la lógica detrás del agrupamiento y desambiguación en Rosario, ya que duda de la coherencia física de saltar de la Facultad de Económicas al Estadio Marcelo Bielsa (que distan unos kilómetros) en un lapso de minutos basándose en las mismas coordenadas o similares, y cómo la foto sin GPS se agrupó.";

  const userPrompt = `CONSULTA:\n${query}\n\nCONTEXTO:\n${context}`;
  
  try {
    const response = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
    fs.writeFileSync("architect_explanation.md", response, "utf8");
    console.log("✅ Explicación escrita a architect_explanation.md");
  } catch (error) {
    console.error("❌ Falló la consulta al Arquitecto:", error.message);
  }
}

askArchitect();
