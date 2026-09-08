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

  console.log("Consultando al Arquitecto sobre el plan de OneDrive y extracción de datos...");
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
    } else {
      const errText = await response.text();
      console.error(`Gemini API error (status ${response.status}): ${errText}`);
    }
  } catch (error) {
    console.error("Error Gemini:", error.message);
  }

  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (!openRouterKey) throw new Error("No API key available");

  const models = [
    "meta-llama/llama-3-8b-instruct:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "google/gemini-2.5-pro:free"
  ];

  for (const model of models) {
    console.log(`Intentando OpenRouter con modelo: ${model}...`);
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
        const errText = await response.text();
        console.error(`OpenRouter error para ${model}: ${errText}`);
      }
    } catch (err) {
      console.error(`Error de red con ${model}: ${err.message}`);
    }
  }

  return "No response (Todos los modelos de OpenRouter fallaron)";
}

const userPrompt = `CONSULTA: Necesitamos implementar una solución robusta y segura para el procesamiento de fotos y documentos de OneDrive. El usuario tiene los siguientes requisitos estrictos:

1. **Verificación de Duplicados en OneDrive**:
   - Escaneamos 5,032 fotos/videos en OneDrive, pero el primer escaneo reportó 0 duplicados. Esto es altamente sospechoso porque el usuario cree que sí hay duplicados con sus backups históricos en el disco F:/G:.
   - El problema puede ser que la base de datos "photo_catalog.db" tiene rutas en minúsculas/mayúsculas o que los tamaños de archivos difieren ligeramente debido a metadatos de sincronización, o que las fotos de WhatsApp tienen nombres modificados (ej. "WhatsApp Image YYYY-MM-DD...") pero son visualmente idénticas a las fotos de la cámara original en F: o G:.
   - ¿Cómo debemos estructurar un algoritmo de verificación robusto que busque coincidencias por múltiples factores (ej. fecha de toma exacta, nombre base del archivo, hash parcial si el archivo está descargado, o agrupamiento temporal-espacial H3)?

2. **Borrado Seguro o Informe**:
   - Si se detectan duplicados, debemos proporcionar un reporte exhaustivo antes de borrar nada, garantizando que el archivo original existe al 100% y de forma accesible en el disco F: o G:. ¿Cuáles son tus pautas para el borrado seguro o la generación de este informe?

3. **Copia de Fotos Únicas a F: en carpetas respectivas (Año/Mes)**:
   - Para las fotos de OneDrive que resulten ser verdaderamente ÚNICAS (que no estén en F: ni G:), debemos copiarlas a F: en sus respectivas carpetas por Año y Mes (ej. F:\\2020\\Enero\\).
   - ¿Cómo debemos organizar esta copia estructurada garantizando que no se pierdan datos y que se actualice la base de datos "photo_catalog.db" con estos nuevos registros?

4. **Extracción del documento bloqueado "רודוס◄ כרתים - אגיוס ניקולאוס.docx" (Rhodes/Crete 2019)**:
   - Hay un documento de Word de 6.5 MB en la cuenta Strauss-Group que no abre por problemas de cuenta/sincronización. Necesitamos extraer su texto (itinerarios, hoteles, reservas) para recuperar la historia del viaje "Rodas/Creta 2019".
   - ¿Cómo podemos forzar de manera segura la lectura o extracción de texto plano de este archivo .docx (que es un zip de XMLs por dentro) usando un script en Node o Python?

5. **Alineación de fotos sin metadatos (EXIF)**:
   - Las fotos que no tengan metadatos EXIF pero coincidan en fecha con los documentos de viaje (reservas de vuelos, hoteles, boletas de restaurantes, etc.) deben heredar los datos geográficos de dicho documento (unión por coincidencia temporal y proximidad). ¿Cómo estructuramos esta regla de inferencia?

Por favor, proporciona el diseño de arquitectura detallado y la secuencia de pasos a seguir de forma rígida, incorporando nuestro plan "anti-saturación" de llamadas diferidas (pausas de 15-30 segundos entre ejecuciones).`;

try {
  const response = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
  console.log("\n====== RESPUESTA DEL ARQUITECTO ======\n");
  console.log(response);
  console.log("\n======================================\n");
  fs.writeFileSync("architect-onedrive-plan-response.md", response, "utf8");
} catch (error) {
  console.error("❌ Falló la consulta al Arquitecto:", error.message);
}