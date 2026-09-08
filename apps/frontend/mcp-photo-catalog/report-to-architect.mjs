import "dotenv/config";
import fs from "fs";

const ARCHITECT_SYSTEM_PROMPT = `Eres un Ingeniero de Software Senior y Arquitecto de Soluciones GIS especializado en Sistemas de Información Geográfica y optimización de APIs de Geolocalización (Overpass API / OpenStreetMap). Actúas como el "Arquitecto de Reverse Geocoding" para el proyecto.

Tus directivas de arquitectura obligatorias son:
1. Diseño Modular y Desacoplado.
2. Formato de Salida Interoperable: Toda interacción técnica DEBE finalizar con un bloque claro "INSTRUCCIÓN PARA EL AGENTE".

Tono de comunicación: Profesional, estratégico, directo. Responde en Castellano.`;

async function callGeminiAPI(systemPrompt, userPrompt) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (apiKey) {
    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
    try {
      console.log("Enviando informe al Arquitecto via Gemini API...");
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

  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (openRouterKey) {
    console.log("Enviando informe al Arquitecto via OpenRouter...");
    const freeModels = [
      "google/gemini-2.0-flash-lite-preview-02-05:free",
      "meta-llama/llama-3.3-70b-instruct:free",
      "deepseek/deepseek-r1:free"
    ];

    for (const model of freeModels) {
      try {
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${openRouterKey}`,
          },
          body: JSON.stringify({
            model: model,
            messages: [
              { role: "system", content: ARCHITECT_SYSTEM_PROMPT },
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
        }
      } catch (e) {
        console.log(`Error con ${model}:`, e.message);
      }
    }
  }

  throw new Error("No fue posible enviar el reporte al Arquitecto.");
}

const userPrompt = `Estimado Arquitecto,

Le informo que hemos completado la ejecución del pipeline de enriquecimiento geográfico masivo con Overpass API (OpenStreetMap) y fallback a Photon API, siguiendo rigurosamente sus directivas de arquitectura y control de saturación.

### Resultados del Enriquecimiento (SQLite: photo_catalog.db)
- **Total de fotos en base de datos:** 34,992 fotos
- **Fotos con coordenadas GPS válidas:** 6,754 fotos
- **Fotos enriquecidas exitosamente con POI/lugar:** **6,745 fotos (99.9% de cobertura GPS)**
- **Fotos pendientes/sin POI en 250m:** Únicamente 9 fotos (áreas aisladas o sin POI registrado en OSM)
- **Total de clusters espaciales procesados (~100m):** 119 clusters
- **Pacing y Resiliencia:** Cumplimiento del delay obligatorio de 1.1s entre llamadas, control de batches de 50, persistencia de estado en \`overpass_clusters_progress\` y reintentos automáticos.

Ejemplos de POIs/Lugares turísticos asignados masivamente en el catálogo:
- *"Blejski Vintgar"* (Garganta de Vintgar, Eslovenia - 188 fotos)
- *"Bohinjsko jezero"* (Lago Bohinj, Eslovenia - 70 fotos)
- *"Patagonia Suites & Apart"* (El Calafate, Argentina - 53 fotos)
- *"Spomenik Francetu Prešernu"* (Ljubljana, Eslovenia - 20 fotos)
- *"Lake Bled"* (Lago Bled, Eslovenia - 14 fotos)
- *"Hotel Brunelleschi Firenze"* (Florencia, Italia - 9 fotos)

### Estado Actual del Sistema
Todo el catálogo de fotos geolocalizadas cuenta ahora con nombres de lugares turísticos, ciudades y países perfectamente normalizados. El sistema de importación a la aplicación Web Hub de Viajes (\`run-import-pipeline.mjs\`) está listo para utilizar estos metadatos enriquecidos.

Por favor evalúe el informe de resultados y proporcione sus directivas e INSTRUCCIÓN PARA EL AGENTE sobre los siguientes pasos recomendados para la integración final con el frontend o las actividades de cierre.`;

async function main() {
  try {
    const response = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
    console.log("\n=================== RESPUESTA Y DIRECTIVAS DEL ARQUITECTO ===================\n");
    console.log(response);
    console.log("\n==============================================================================\n");

    fs.writeFileSync("architect-final-geoprocessing-report.md", response, "utf8");
    console.log("Reporte final guardado en architect-final-geoprocessing-report.md");
  } catch (error) {
    console.error("Error al enviar el reporte al Arquitecto:", error.message);
  }
}

main();
