import "dotenv/config";
import fs from "fs";
import path from "path";

const ARCHITECT_SYSTEM_PROMPT = `Eres un Ingeniero de Software Senior y Arquitecto de Soluciones GIS especializado en Sistemas de Información Geográfica y optimización de APIs de Geolocalización. Actúas como el "Arquitecto de Reverse Geocoding" para el proyecto "Reverse Geocoding & Consensus Truth Engine".

Tus directivas de arquitectura obligatorias son:
1. Diseño Modular y Desacoplado: Divide tareas complejas (como inferencia de "Verdad del Lugar" o Azimut) en micro-módulos aislados y testeables paso a paso sin saturar la ventana de contexto del Agente Programador (AntiGravity).
2. Eficiencia de Datos y Soberanía Local (SpatialCache): Prioriza siempre la "Caché Espacial" local (como PostGIS/SQLite) y agrupamiento de coordenadas por índices hexagonales H3 (Resolución 9) antes de llamar a APIs externas pagadas (Google Maps, Cloud Vision). Si se resuelve en un hexágono, las consultas subsiguientes dentro de 15 minutos heredan la ubicación (tolerancia cero al desperdicio de peticiones de red).
3. Sinergia de Conocimiento (NotebookLM): Actúa como estratega de alto nivel. Para sintaxis exacta o documentación profunda de configuración, delega o indica consultar la "Fuente de Verdad" (NotebookLM) vía MCP.
4. Formato de Salida Interoperable: Toda interacción técnica DEBE finalizar obligatoriamente con un bloque claro, autocontenido y procesable etiquetado como "INSTRUCCIÓN PARA EL AGENTE" que el agente de IA (AntiGravity) pueda ejecutar directamente sin interpretación del usuario.

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
      console.log(`⚠️ Gemini API nativa retornó estado ${response.status}. Iniciando failover a OpenRouter...`);
    }
  } catch (error) {
    console.log(`⚠️ Error al llamar a Gemini API nativa: ${error.message}. Iniciando failover a OpenRouter...`);
  }

  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (!openRouterKey) {
    throw new Error("Ambos métodos fallaron: Gemini API nativa dio error de cuota/red y OPENROUTER_API_KEY no está configurada en .env.");
  }

  let openRouterModels = [
    "liquid/lfm-2.5-1.2b-instruct:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "openrouter/free",
    "google/gemini-2.5-flash:free"
  ];

  if (process.env.OPENROUTER_FALLBACK_MODELS) {
    openRouterModels = process.env.OPENROUTER_FALLBACK_MODELS.split(",").map(m => m.trim());
  }

  console.log("Intentando llamar a través de OpenRouter...");
  for (const model of openRouterModels) {
    try {
      console.log(`Intentando con modelo OpenRouter: ${model}...`);
      const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${openRouterKey}`,
          "HTTP-Referer": "https://localhost:3000",
          "X-Title": "Reverse Geocoding Architect Bridge"
        },
        body: JSON.stringify({
          model: model,
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
          console.log(`✅ Conexión exitosa con OpenRouter usando el modelo ${model}.`);
          return data.choices[0].message.content;
        }
      } else {
        const errDetail = await response.text();
        console.log(`⚠️ OpenRouter falló con modelo ${model} (status ${response.status}): ${errDetail}`);
      }
    } catch (err) {
      console.log(`⚠️ Error con modelo OpenRouter ${model}: ${err.message}`);
    }
  }

  throw new Error("Fallo crítico: No se pudo obtener respuesta de la API de Gemini nativa ni de OpenRouter.");
}

async function askArchitect() {
  const query = "Hola Arquitecto. El usuario flier me pide que me asesore contigo ya que tienes otra propuesta para avanzar en el desarrollo. ¿Cuál es tu propuesta detallada sobre cómo deberíamos proceder ahora para el proyecto?";
  const context = `Acabamos de implementar la versión 8.0 que incluye la Capa de Veto y Alineación Visual-Semántica (evitando que fotos de interiores de iglesias en Rosario se resuelvan erróneamente como 'Monumento a la Bandera' y en su lugar sugiriendo la Catedral). Las pruebas pasaron con éxito. El usuario tiene abierto walkthrough.md en la sección 'Cola de Operadores HITL y Toasts Premium (Antigravity 2.0)' con la observación 'Para avanzar quiero que te asesores con mi gem, el tiene otra propuesta'.`;

  const userPrompt = `CONSULTA:\n${query}\n\nCONTEXTO:\n${context}`;
  
  try {
    const response = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
    console.log("\n====== RESPUESTA DEL ARQUITECTO ======\n");
    console.log(response);
    console.log("\n======================================\n");
    
    // Write answer to a markdown file for the user to read or for us to review
    fs.writeFileSync("architect_proposal.md", response, "utf8");
  } catch (error) {
    console.error("❌ Falló la consulta al Arquitecto:", error.message);
  }
}

askArchitect();
