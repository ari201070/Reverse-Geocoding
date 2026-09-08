import "dotenv/config";
import fs from "fs";

const ARCHITECT_SYSTEM_PROMPT = `Eres un Ingeniero de Software Senior y Arquitecto de Soluciones GIS especializado en Sistemas de Información Geográfica y optimización de APIs de Geolocalización (Overpass API / OpenStreetMap). Actúas como el "Arquitecto de Reverse Geocoding" para el proyecto.

Tus directivas de arquitectura obligatorias son:
1. Diseño Modular y Desacoplado: Divide tareas complejas en micro-módulos aislados.
2. Control de Saturación y Pacing: Respeta la cuota de Overpass API (delay 1s entre clusters, batches de 50, reintentos exponenciales).
3. Formato de Salida Interoperable: Toda interacción técnica DEBE finalizar con un bloque claro "INSTRUCCIÓN PARA EL AGENTE".

Tono de comunicación: Profesional, estratégico, directo. Responde en Castellano.`;

async function callGeminiAPI(systemPrompt, userPrompt) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (apiKey) {
    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
    try {
      console.log("Consultando al Arquitecto via Gemini API...");
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
      } else {
        console.log(`Gemini API HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("Error Gemini:", error.message);
    }
  }

  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (openRouterKey) {
    console.log("Consultando al Arquitecto via OpenRouter...");
    const freeModels = [
      "google/gemini-2.0-flash-lite-preview-02-05:free",
      "meta-llama/llama-3.3-70b-instruct:free",
      "deepseek/deepseek-r1:free",
      "qwen/qwen-2.5-72b-instruct:free"
    ];

    for (const model of freeModels) {
      try {
        console.log(`Intentando modelo ${model}...`);
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

  throw new Error("No fue posible consultar al Arquitecto en ningún proveedor.");
}

const userPrompt = `Estimado Arquitecto,

Hemos recibido la instrucción de enriquecer el catálogo de fotos utilizando la API de Overpass (OpenStreetMap) con la siguiente estrategia:

### Métricas Dinámicas del Catálogo (SQLite: photo_catalog.db)
- Total de fotos en base de datos: 34,992
- Fotos con coordenadas GPS válidas: 6,754
- Fotos con GPS que carecen de 'location_name': 1,241
- Total de clusters espaciales únicos (~100m, ROUND(lat, 3), ROUND(lon, 3)): 119 clusters

### Estrategia de Procesamiento y Pacing Propuesta
1. **Agrupamiento Geográfico:** Agrupar las 1,241 fotos sin location_name en 119 clusters (~100m).
2. **Queue de Clusters:** Ordenar clusters de mayor a menor según cantidad de fotos.
3. **Consulta Overpass (por Cluster):**
   - Query Overpass QL: Nodos/Vías/Relaciones con etiquetas \`tourism\`, \`natural\`, \`peak\`, \`route\`, \`historic\`, \`amenity\` dentro de un radio de 250m (\`around:250, lat, lon\`).
   - Pacing: Delay obligatorio de 1.0 segundo entre llamadas a Overpass para respetar políticas de uso libre y evitar HTTP 429.
   - Batch size: Lotes de 50 clusters con persistencia del progreso en una tabla de estado en SQLite (\`overpass_clusters_progress\`).
4. **Bulk Update:** Asignación masiva del nombre del POI encontrado a todas las fotos asociadas a cada cluster (\`UPDATE photos SET location_name = ? WHERE ROUND(latitude, 3) = ? AND ROUND(longitude, 3) = ?\`).
5. **Alineación con Cooldown.md:** Respeto estricto del delay entre batches y pacing entre solicitudes.

Por favor evalúa esta estrategia, valida la consulta Overpass QL recomendada, y proporciona la INSTRUCCIÓN PARA EL AGENTE para proceder con la ejecución del script.`;

async function main() {
  try {
    const response = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
    console.log("\n=================== RESPUESTA DEL ARQUITECTO ===================\n");
    console.log(response);
    console.log("\n================================================================\n");

    fs.writeFileSync("architect-overpass-response.md", response, "utf8");
    console.log("Respuesta guardada en architect-overpass-response.md");
  } catch (error) {
    console.error("Error al consultar al Arquitecto:", error.message);
  }
}

main();
