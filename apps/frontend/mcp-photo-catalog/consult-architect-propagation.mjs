import "dotenv/config";
import fs from "fs";

const ARCHITECT_SYSTEM_PROMPT = `Eres un Ingeniero de Software Senior y Arquitecto de Soluciones GIS especializado en Clasificación Multimodal de Catálogos Fotograficos y Análisis Contextual de Metadatos. Actúas como el "Arquitecto de Reverse Geocoding" para el proyecto.

Tus directivas de arquitectura obligatorias son:
1. Diseño Modular y Desacoplado: Soluciones basadas en capas de inferencia.
2. Propagación Contextual y Soberanía Local: Priorizar metadatos de carpetas, proximidad temporal e inferencia de viajes conocidos antes de dejar campos nulos.
3. Formato de Salida Interoperable: Toda interacción técnica DEBE finalizar con un bloque claro "INSTRUCCIÓN PARA EL AGENTE".

Tono de comunicación: Profesional, estratégico, directo. Responde en Castellano.`;

async function callArchitectWithFailover(systemPrompt, userPrompt) {
  const openRouterKey = process.env.OPENROUTER_API_KEY;
  const freeModels = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free"
  ];

  if (openRouterKey) {
    for (const model of freeModels) {
      try {
        console.log(`Consultando al Arquitecto via OpenRouter con modelo: ${model}...`);
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${openRouterKey}`,
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
            return data.choices[0].message.content;
          }
        } else {
          console.log(`HTTP ${response.status} en modelo ${model}`);
        }
      } catch (e) {
        console.log(`Error con ${model}:`, e.message);
      }
    }
  }

  // Si falla OpenRouter, probar Gemini API
  const apiKey = process.env.GEMINI_API_KEY;
  if (apiKey) {
    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
    try {
      console.log("Probrando Gemini API...");
      const response = await fetch(geminiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ role: "user", parts: [{ text: userPrompt }] }],
          systemInstruction: { parts: [{ text: systemPrompt }] },
          generationConfig: { temperature: 0.2, maxOutputTokens: 8192 }
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
  }

  throw new Error("No fue posible consultar al Arquitecto.");
}

const userPrompt = `Estimado Arquitecto,

El usuario nos ha señalado una inconsistencia crítica en la clasificación de las 34,992 fotos del catálogo:

### Diagnóstico del Problema
1. Actualmente, **29,404 de las 34,992 fotos (84%)** tienen \`country\` y \`city\` como NULL en la base de datos porque el motor previo dependía exclusivamente de que la foto individual tuviera coordenadas GPS EXIF.
2. **Caso Real de Ejemplo:**
   - Foto A (\`2023-10-07 11.53.37.jpg\`): Ubicada en \`F:\\2023\\Octubre\\גברים רעבים באיטליה-2023\\פיזה\\\`. Tenía GPS -> Clasificada como Italia, Pisa, Piazza del Duomo (Torre de Pisa).
   - Foto B (\`2023-10-07 11.52.21_IMG...\`): Ubicada en \`F:\\2023\\Octubre\\גברים רעבים באיטליה-2023\\xiomi\\\`. Tomada **1 minuto antes** (11:52) en la misma ciudad/viaje, pero sin GPS EXIF en la foto -> Quedó como NULL / Sin clasificar.
3. **Metadatos no aprovechados:**
   - La estructura de directorios contiene información explícita en Hebreo, Español e Inglés: ej. \`גברים רעבים באיטליה-2023\` (Italia 2023), \`טיול לארגנטינה\` (Viaje a Argentina), \`לאגו פואלו\` (Lago Puelo), \`Bosnia I Herzegobina\`, \`פיזה\` (Pisa).
   - Existen viajes conocidos verificados por documentos (\`KnownTrips.js\`).

### Propuesta de Arquitectura: Motor de Propagación Contextual en 3 Capas
Proponemos un pipeline masivo en SQLite para completar los metadatos de las 29,404 fotos faltantes:

1. **Capa 1: Inferencia Lingüística de Carpetas y Nombres de Archivos (Path Parsing)**
   - Parsear nombres de carpetas en Hebreo/Español/Inglés e identificar País/Ciudad/Evento por diccionarios y expresiones regulares.

2. **Capa 2: Propagación Temporal por Proximidad Misma Carpeta / Mismo Día**
   - Para cualquier foto sin GPS, si pertenece a la misma carpeta padre (o subcarpeta hermana) y fue tomada el mismo día/hora que fotos con ubicación conocida, hereda el \`country\`, \`city\` y \`location_name\` del grupo.

3. **Capa 3: Mapeo por Rango de Fechas con KnownTrips**
   - Si la fecha de toma cae dentro del rango de fechas de un viaje conocido (ej. Italia 2023: Oct 3-11), asignar el país y vincular al viaje.

Por favor evalúa esta arquitectura, proporciona las pautas de implementación y la INSTRUCCIÓN PARA EL AGENTE para ejecutar esta solución integral.`;

async function main() {
  try {
    const response = await callArchitectWithFailover(ARCHITECT_SYSTEM_PROMPT, userPrompt);
    console.log("\n=================== RESPUESTA Y DIRECTIVAS DEL ARQUITECTO ===================\n");
    console.log(response);
    console.log("\n==============================================================================\n");

    fs.writeFileSync("architect-contextual-propagation-plan.md", response, "utf8");
    console.log("Plan del Arquitecto guardado en architect-contextual-propagation-plan.md");
  } catch (error) {
    console.error("Error al consultar al Arquitecto:", error.message);
  }
}

main();
