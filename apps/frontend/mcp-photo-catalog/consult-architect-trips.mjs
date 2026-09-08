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

  console.log("Consultando al Arquitecto...");
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

const userPrompt = `CONSULTA: Necesito definir la estructura correcta de viajes/actividades para importar fotos como documentos de viaje.

DATOS REALES DE LA BASE DE DATOS (photo_catalog.db):

**Viajes internacionales confirmados con documentación:**

1. **Argentina 2011-2012**: 4,838 fotos (Nov 7, 2011 - Ene 3, 2026)
   - Ciudades: Calafate, Trevelin, Los Antiguos, Cerro Campanario, Lago Puelo, Gobernador Costa, Cueva de las Manos, Glaciar Perito Moreno, Caleta Valdés, Puerto Pirámides
   - Documento: Booking_BuenosAires_2011_HotelMundial.png
   - Nota: Las fotos con fecha 2026 son probablemente fechas de subida/actualización

2. **Argentina 2025**: 30 días (Sep 26 - Oct 30, 2025)
   - Itinerario completo: Buenos Aires, Tigre, Rosario, Villa Traful, Bariloche, El Bolsón, Mendoza, Puente del Inca, Salta, Iguazú, Esteros del Iberá, Corrientes
   - Documentos: itinerary_Y0HBMB59-1.pdf,Booking.com screenshots, tickets de vuelo
   - Referencia: F:\\Documentos_Viaje\\2025\\

3. **Eslovenia 2015**: 355 fotos (Jul 2-6, 2015)
   - Ciudades: Bled, Podhom, Ribčev Laz, Ukanc, Bohinjska Bistrica, Stara Fužina, Bohinjska Bela
   - Documentos: 4 reservas de hotel (ApartmentsZorc, GarniHotelAzur, HotelKrim, HotelSavica)
   - Referencia: F:\\Documentos_Viaje\\2015\\Julio\\

4. **Grecia/Crete 2013**: 9 fotos (Jul 23-27, 2013)
   - Ciudades: Δημοτική Ενότητα Χερσονήσου (Chersonissos), Ψυχρό, Δημοτική Ενότητα Ηρακλείου
   - NOTA: Todas las fotos están en Creta, no en Grecia continental

5. **Croacia+Montenegro 2010**: 161 fotos (Jun 24-30, 2010)
   - Ciudades: Dubrovnik (Croacia), Podgorica, Kolašin, Budva, Velji Bostur, Kotor, Škaljari (Montenegro)

6. **Italia 2023**: 70 fotos (Oct 6-7, 2023)
   - Solo Firenze y Pisa (viaje corto de 2 días)
   - Documentos: G:\\האחסון שלי\\גברים רעבים באיטליה\\

7. **Bosnia 2023**: 1 foto (May 4, 2023)
   - Documento:BIH 2304 טבלת מלונות וטיסות עבור אריאל פליאר.pdf
   - Referencia: F:\\Documentos_Viaje\\2023\\Mayo\\

**Visitas locales (NO son viajes internacionales):**
- Israel 2008: Dec 2-6 (Negev desert trip) - 27 fotos
- Israel 2010: Jan 9 (Nachal Dror hike) - 4 fotos
- Israel 2010: Jan 15 (Eilat archaeology) - 2 fotos
- Israel 2011: Sep 10 (Ashdod beach) - 7 fotos
- Israel 2017: Aug 20 - Oct 5 (various local visits)
- Israel 2025: Sep 1-25 (Tel Aviv, mostly screenshots)

**PROBLEMAS IDENTIFICADOS:**
1. El script actual agrupa "Greece" cuando debería ser "Crete" (Κρήτη)
2. Algunas fotos tienen fechas de subida/actualización, no de toma real
3. Las visitas locales de Israel no deberían ser "viajes internacionales"
4. El viaje a Italia 2023 fue solo Firenze+Pisa (2 días), no todo Italia
5. Bosnia 2023 tiene solo 1 foto geolocalizada, pero hay documentos de viaje

**PREGUNTA:**
¿Cómo deberíamos estructurar los viajes/actividades para el importador de fotos? Considerando:
- Usar booking documents como fuente de verdad para fechas reales
- Distinguir entre "viajes internacionales" y "visitas locales/actividades"
- Manejar fotos con fechas incorrectas (subida vs toma)
- La estructura debe ser compatible con el sistema de la app (TravelBooking type)
- Los datos de booking están en F:\\Documentos_Viaje\\ y G:\\`;

try {
  const response = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
  console.log("\n====== RESPUESTA DEL ARQUITECTO ======\n");
  console.log(response);
  console.log("\n======================================\n");
  fs.writeFileSync("architect-trips-response.md", response, "utf8");
} catch (error) {
  console.error("❌ Falló la consulta:", error.message);
}