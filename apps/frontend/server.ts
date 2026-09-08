import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import dotenv from "dotenv";
import { exec } from "child_process";
import { initDatabase, insertAnchor, generateAnchorId, closeDatabase } from "./src/db.js";
import { getH3Index, checkLocationCache, updateSpatialCache } from "./src/spatial_cache.js";
import { generateContentWithRetry, formatGeminiError } from "./src/gemini.js";
import { PDFParse } from "pdf-parse";

const LOCAL_VOUCHER_SERVICE = process.env.LOCAL_VOUCHER_SERVICE || "http://localhost:8000";

dotenv.config();

const GEOCODE_API_URL = process.env.GEOCODE_API_URL || "http://localhost:3001/api/geocode";

const app = express();
app.use(express.json({ limit: '20mb' }));

const PORT = 3000;

// API routes FIRST
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", time: new Date().toISOString() });
});

// Endpoint to resolve public Google Photos sharing links
app.post("/api/resolve-photo-link", async (req, res) => {
  try {
    const { link } = req.body;
    if (!link) {
      return res.status(400).json({ error: "Falta el enlace" });
    }

    console.log(`Resolving Google Photos link: ${link}`);
    
    // Fetch the link to resolve redirect and get the page HTML
    const response = await fetch(link, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
      }
    });

    if (!response.ok) {
      return res.status(400).json({ error: "No se pudo acceder al enlace de Google Fotos. Verifica que sea un enlace público." });
    }

    const html = await response.text();

    // Look for og:image meta tag
    const ogImageMatch = html.match(/<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']/i) ||
                         html.match(/<meta\s+content=["']([^"']+)["']\s+property=["']og:image["']/i);

    let directUrl = "";
    if (ogImageMatch) {
      directUrl = ogImageMatch[1];
    } else {
      // Fallback: look for googleusercontent images inside the HTML
      const imgRegex = /"https:\/\/lh3\.googleusercontent\.com\/[a-zA-Z0-9_-]+"/g;
      const matches = html.match(imgRegex);
      if (matches && matches.length > 0) {
        directUrl = matches[0].replace(/"/g, '');
      }
    }

    if (!directUrl) {
      return res.status(400).json({ error: "No se pudo extraer la imagen del enlace. Asegúrate de que sea un enlace válido y público de Google Fotos." });
    }

    // Strip size modifiers from the end to get clean baseUrl
    if (directUrl.includes('=')) {
      const parts = directUrl.split('=');
      if (parts[parts.length - 1].match(/^[a-zA-Z0-9-]+$/i)) {
        directUrl = parts.slice(0, -1).join('=');
      }
    }

    console.log(`Successfully resolved to direct image URL: ${directUrl}`);

    return res.json({
      id: 'photo-resolved-' + Math.random().toString(36).substring(2, 11),
      name: 'Foto de Viaje Compartida.jpg',
      mimeType: 'image/jpeg',
      webViewLink: link,
      iconLink: directUrl,
      source: 'photos',
      baseUrl: directUrl
    });

  } catch (err: any) {
    console.error("Error resolving photos link:", err);
    res.status(500).json({ error: "Error al procesar el enlace de Google Fotos: " + err.message });
  }
});

// Proxy helper: forward file to local voucher extraction service
const TIMEOUT_MS = 300000; // 5 minutos para procesamiento en CPU lenta

async function callLocalVoucherService(fileBuffer: Buffer, fileName: string, mimeType: string): Promise<any> {
  const formData = new FormData();
  const blob = new Blob([fileBuffer], { type: mimeType });
  formData.append("file", blob, fileName);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(`${LOCAL_VOUCHER_SERVICE}/api/extract-voucher`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`Local voucher service returned ${response.status}: ${errorText}`);
    }

    return response.json();
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new Error(`Local voucher service timed out after ${TIMEOUT_MS / 1000} seconds`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Map local service response to the format the frontend expects
function mapVoucherToBooking(voucher: any, name: string): any {
  const title = voucher.location_name || name;
  const location = voucher.address ? `${title}, ${voucher.address}` : title;

  return {
    isTravelDocument: true,
    category: voucher.category || "activity",
    supplier: voucher.supplier || "",
    title: title,
    startDate: voucher.start_date || null,
    startTime: voucher.start_time || null,
    endDate: null,
    endTime: null,
    confirmationNumber: null,
    location: location,
    coordinates: voucher.latitude && voucher.longitude ? {
      lat: voucher.latitude,
      lng: voucher.longitude
    } : null,
    extraction_notes: "Extraído y geolocalizado localmente",
    passengerOrGuestName: null,
    price: voucher.amount || null,
    currency: voucher.currency || null,
    details: null,
    summary: voucher.summary || `Evento/Voucher detectado: ${title}`,
  };
}

// Check local service health
async function checkLocalServiceHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${LOCAL_VOUCHER_SERVICE}/api/health`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

// PDF Extraction & Local Llama 3.2 (Ollama) Processing Helpers
async function extractTextFromPDF(pdfBuffer: Buffer): Promise<string> {
  try {
    const parser = new PDFParse({ data: pdfBuffer });
    await (parser as any).load();
    const pdfData = await parser.getText();
    const text = pdfData.text || "";
    parser.destroy();
    return text;
  } catch (err: any) {
    console.warn("[PDFParse] Fallback usando importación dinámica de pdf-parse:", err.message);
    try {
      const pdfModule = await import("pdf-parse");
      const parseFunc = (pdfModule as any).default || pdfModule;
      if (typeof parseFunc === "function") {
        const data = await parseFunc(pdfBuffer);
        return data.text || "";
      }
    } catch (fallbackErr: any) {
      console.error("[PDFParse] Falló la extracción de PDF:", fallbackErr.message);
    }
    return "";
  }
}

async function analyzeTextWithLlama(text: string): Promise<{
  location_name?: string;
  datetime?: string;
  amount?: number | string;
  currency?: string;
}> {
  const ollamaBaseUrl = process.env.OLLAMA_BASE_URL || "http://localhost:11434";
  const prompt = `Analiza este texto extraído de un documento de viaje y extrae estrictamente un objeto JSON con los siguientes campos:
- 'location_name': nombre del hotel, aerolínea, parque o lugar del evento.
- 'datetime': fecha y hora del evento (YYYY-MM-DD HH:MM).
- 'amount': monto total de la transacción.
- 'currency': moneda utilizada (ARS, USD, EUR, etc.).
Responde ÚNICAMENTE con el objeto JSON, sin introducciones ni bloques de código.

Texto del documento:
${text.slice(0, 15000)}`;

  const modelsToTry = ["llama3.2:latest", "llama3.2", "llama3.2:3b", "qwen2.5-coder:7b"];
  
  let rawResponse = "";
  let lastError = "";

  for (const model of modelsToTry) {
    try {
      console.log(`[Ollama] Consultando modelo ${model}...`);
      const res = await fetch(`${ollamaBaseUrl}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model,
          prompt,
          stream: false,
          format: "json"
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.response) {
          rawResponse = data.response;
          console.log(`[Ollama] Respuesta obtenida exitosamente con modelo ${model}`);
          break;
        }
      } else {
        lastError = `Status ${res.status}: ${await res.text()}`;
      }
    } catch (err: any) {
      lastError = err.message;
      console.warn(`[Ollama] Error al conectar con ${model}:`, err.message);
    }
  }

  if (!rawResponse) {
    throw new Error(`No se pudo obtener inferencia de Ollama (Llama 3.2). Verifique que Ollama esté ejecutándose en el puerto 11434. (${lastError})`);
  }

  let cleanJson = rawResponse.trim();
  if (cleanJson.startsWith("```")) {
    cleanJson = cleanJson.replace(/^```(?:json)?/i, "").replace(/```$/, "").trim();
  }

  try {
    return JSON.parse(cleanJson);
  } catch (parseErr) {
    console.error("[Ollama] Error parseando JSON devuelto por Llama:", rawResponse);
    return {
      location_name: undefined,
      datetime: undefined,
      amount: undefined,
      currency: undefined
    };
  }
}

async function resolveLocationGeocoding(locationName: string) {
  if (!locationName) return { coordinates: null, h3_index: null };
  
  try {
    const cached = checkLocationCache(locationName);
    if (cached) {
      const lat = cached.latitude;
      const lng = cached.longitude;
      const h3 = getH3Index(lat, lng);
      return { coordinates: { lat, lng }, h3_index: h3 };
    }

    const geoResponse = await fetch(`${GEOCODE_API_URL}?address=${encodeURIComponent(locationName)}`);
    if (geoResponse.ok) {
      const geoData = await geoResponse.json();
      if (geoData.lat && geoData.lng) {
        const lat = parseFloat(Number(geoData.lat).toFixed(4));
        const lng = parseFloat(Number(geoData.lng).toFixed(4));
        const h3 = getH3Index(lat, lng);
        updateSpatialCache(h3, locationName, lat, lng);
        return { coordinates: { lat, lng }, h3_index: h3 };
      }
    }
  } catch (geoErr: any) {
    console.warn("[Geocoding] No se pudo geocodificar la ubicación:", geoErr.message);
  }

  return { coordinates: null, h3_index: null };
}

function parseDatetime(datetimeStr?: string | null): { startDate: string | null; startTime: string | null } {
  if (!datetimeStr || typeof datetimeStr !== 'string') {
    return { startDate: null, startTime: null };
  }
  const trimmed = datetimeStr.trim();
  const match = trimmed.match(/^(\d{4}-\d{2}-\d{2})[T\s]?(\d{2}:\d{2})?/);
  if (match) {
    return {
      startDate: match[1] || null,
      startTime: match[2] || null
    };
  }
  const dateMatch = trimmed.match(/\d{4}-\d{2}-\d{2}/);
  const timeMatch = trimmed.match(/\d{2}:\d{2}/);
  return {
    startDate: dateMatch ? dateMatch[0] : null,
    startTime: timeMatch ? timeMatch[0] : null
  };
}

function parseAmount(amountVal: any): number | null {
  if (amountVal === null || amountVal === undefined) return null;
  if (typeof amountVal === 'number') return amountVal;
  if (typeof amountVal === 'string') {
    const cleaned = amountVal.replace(/[^0-9.,]/g, '').replace(',', '.');
    const num = parseFloat(cleaned);
    return isNaN(num) ? null : num;
  }
  return null;
}

async function processPdfDocument(fileBuffer: Buffer, fileName: string): Promise<any> {
  console.log(`[PDF Pipeline] Extrayendo texto plano de PDF: "${fileName}"`);
  
  const pdfText = await extractTextFromPDF(fileBuffer);
  if (!pdfText || pdfText.trim().length === 0) {
    throw new Error("No se pudo extraer texto del PDF (archivo vacío o imagen escaneada sin capa de texto)");
  }

  console.log(`[PDF Pipeline] Texto extraído (${pdfText.length} chars). Enviando a Llama 3.2 en Ollama...`);

  const llamaResult = await analyzeTextWithLlama(pdfText);
  const locationName = llamaResult.location_name || fileName.replace(/\.pdf$/i, '');
  const { startDate, startTime } = parseDatetime(llamaResult.datetime);
  const amount = parseAmount(llamaResult.amount);
  const currency = llamaResult.currency || "USD";

  const { coordinates, h3_index } = await resolveLocationGeocoding(locationName);

  const parsedResult = {
    isTravelDocument: true,
    category: "activity",
    supplier: locationName,
    title: locationName,
    startDate,
    startTime,
    endDate: null,
    endTime: null,
    confirmationNumber: null,
    location: locationName,
    coordinates,
    h3_index,
    extraction_notes: "Extraído localmente vía PDF-Parse + Llama 3.2 (Ollama)",
    passengerOrGuestName: null,
    price: amount,
    currency,
    details: null,
    summary: `Voucher detectado: ${locationName}`,
  };

  try {
    const anchorId = generateAnchorId(fileName);
    insertAnchor({
      id: anchorId,
      location: locationName,
      latitude: coordinates?.lat,
      longitude: coordinates?.lng,
      is_travel_document: true,
      h3_index,
      raw_json: JSON.stringify(parsedResult),
    });
  } catch (dbErr: any) {
    console.warn("[DB] Error guardando anchor de PDF:", dbErr.message);
  }

  return parsedResult;
}

// Analyze document endpoint — proxies to local voucher service
app.post("/api/analyze-doc", async (req, res) => {
  try {
    const { fileId, mimeType, name, source, baseUrl } = req.body;
    if (!fileId || !mimeType || !name) {
      return res.status(400).json({ error: "Missing required fields: fileId, mimeType, name" });
    }

    console.log(`[Local] Analyzing file: "${name}" (${mimeType}) - ID: ${fileId} - Source: ${source || 'drive'}`);

    // Check local service availability first
    const isHealthy = await checkLocalServiceHealth();
    if (!isHealthy) {
      return res.status(503).json({
        error: "Servicio local de escaneo no disponible",
        details: `No se pudo conectar con el servidor local de escaneo (${LOCAL_VOUCHER_SERVICE}). Asegúrate de que Uvicorn esté iniciado.`,
        code: "LOCAL_SERVICE_UNAVAILABLE",
      });
    }

    let fileBuffer: Buffer | null = null;

    // Google Drive/Photos download not available in local mode
    // Use /api/analyze-local with base64Data for local file uploads
    if (!fileBuffer) {
      return res.status(400).json({
        error: "Análisis de Drive no disponible en modo local",
        details: "Usa la pestaña 'Subir desde mi PC' para analizar archivos localmente.",
      });
    }

    // Send to local voucher service
    const serviceResponse = await callLocalVoucherService(fileBuffer, name, mimeType);

    if (serviceResponse.status === "success" && serviceResponse.voucher) {
      const parsedResult = mapVoucherToBooking(serviceResponse.voucher, name);

      // Geocode location if available
      if (parsedResult.location) {
        try {
          const cached = checkLocationCache(parsedResult.location);
          if (cached) {
            parsedResult.coordinates = { lat: cached.latitude, lng: cached.longitude };
          } else {
            const geoResponse = await fetch(`${GEOCODE_API_URL}?address=${encodeURIComponent(parsedResult.location)}`);
            if (geoResponse.ok) {
              const geoData = await geoResponse.json();
              if (geoData.lat && geoData.lng) {
                const lat = parseFloat(Number(geoData.lat).toFixed(4));
                const lng = parseFloat(Number(geoData.lng).toFixed(4));
                parsedResult.coordinates = { lat, lng };
                const h3 = getH3Index(lat, lng);
                parsedResult.h3_index = h3;
                updateSpatialCache(h3, parsedResult.location, lat, lng);
              }
            }
          }
        } catch (geoError: any) {
          console.warn("[Geocoding] Servicio local no disponible:", geoError.message);
        }
      }

      // Save anchor
      try {
        const anchorId = generateAnchorId(name);
        insertAnchor({
          id: anchorId,
          location: parsedResult.location,
          latitude: parsedResult.coordinates?.lat,
          longitude: parsedResult.coordinates?.lng,
          is_travel_document: parsedResult.isTravelDocument,
          h3_index: parsedResult.h3_index,
          raw_json: JSON.stringify(parsedResult),
        });
      } catch (dbErr: any) {
        console.warn("[DB] Error registrando anchor en /api/analyze-doc:", dbErr.message);
      }

      return res.json(parsedResult);
    } else {
      throw new Error(serviceResponse.error || "El servicio local no pudo extraer información del voucher.");
    }

  } catch (error: any) {
    console.error("Error analyzing document:", error);
    const isConnectionError = error.message?.includes("fetch") || error.message?.includes("ECONNREFUSED") || error.message?.includes("LOCAL_SERVICE_UNAVAILABLE");
    if (isConnectionError) {
      return res.status(503).json({
        error: "Servicio local de escaneo no disponible",
        details: `No se pudo conectar con el servidor local de escaneo (${LOCAL_VOUCHER_SERVICE}). Asegúrate de que Uvicorn esté iniciado.`,
        code: "LOCAL_SERVICE_UNAVAILABLE",
      });
    }
    res.status(500).json({
      error: "Error en el análisis de documento",
      details: error.message || "Error desconocido al procesar el archivo con el servicio local.",
    });
  }
});

// Analyze local file endpoint — proxies to local voucher service
app.post("/api/analyze-local", async (req, res) => {
  try {
    const { name, mimeType, base64Data, exifData } = req.body;
    if (!name || !mimeType || !base64Data) {
      return res.status(400).json({ error: "Missing required fields: name, mimeType, base64Data" });
    }

    console.log(`[Local] Analyzing local file: "${name}" (${mimeType})`);

    const fileBuffer = Buffer.from(base64Data, 'base64');

    const isPdf = mimeType === 'application/pdf' || name.toLowerCase().endsWith('.pdf');
    if (isPdf) {
      try {
        const pdfResult = await processPdfDocument(fileBuffer, name);
        if (exifData) {
          if (exifData.lat && exifData.lng) {
            pdfResult.coordinates = { lat: exifData.lat, lng: exifData.lng };
            pdfResult.extraction_notes += " (Coordenadas EXIF preservadas)";
          }
          if (exifData.date) {
            const datePart = exifData.date.split('T')[0];
            const timePart = exifData.date.split('T')[1]?.substring(0, 5);
            if (datePart) pdfResult.startDate = datePart;
            if (timePart) pdfResult.startTime = timePart;
            pdfResult.extraction_notes += " (Fecha EXIF preservada)";
          }
        }
        return res.json(pdfResult);
      } catch (pdfErr: any) {
        console.error("[PDF Pipeline] Error:", pdfErr.message);
        return res.status(500).json({
          error: "Error en el análisis de PDF",
          details: pdfErr.message,
        });
      }
    }

    // Check local service availability first (solo no-PDF → moondream :8000)
    const isHealthy = await checkLocalServiceHealth();
    if (!isHealthy) {
      return res.status(503).json({
        error: "Servicio local de escaneo no disponible",
        details: `No se pudo conectar con el servidor local de escaneo (${LOCAL_VOUCHER_SERVICE}). Asegúrate de que Uvicorn esté iniciado.`,
        code: "LOCAL_SERVICE_UNAVAILABLE",
      });
    }

    const serviceResponse = await callLocalVoucherService(fileBuffer, name, mimeType);

    if (serviceResponse.status === "success" && serviceResponse.voucher) {
      const parsedResult = mapVoucherToBooking(serviceResponse.voucher, name);

      // Prioritize EXIF data if available
      if (exifData) {
        if (exifData.lat && exifData.lng) {
          parsedResult.coordinates = { lat: exifData.lat, lng: exifData.lng };
          parsedResult.extraction_notes += " (Coordenadas EXIF preservadas)";
        }
        if (exifData.date) {
          const datePart = exifData.date.split('T')[0];
          const timePart = exifData.date.split('T')[1]?.substring(0, 5);
          if (datePart) parsedResult.startDate = datePart;
          if (timePart) parsedResult.startTime = timePart;
          parsedResult.extraction_notes += " (Fecha EXIF preservada)";
        }
      }

      // Geocode location only if no EXIF coordinates and location name exists
      if (!parsedResult.coordinates && parsedResult.location) {
        try {
          const cached = checkLocationCache(parsedResult.location);
          if (cached) {
            parsedResult.coordinates = { lat: cached.latitude, lng: cached.longitude };
          } else {
            const geoResponse = await fetch(`${GEOCODE_API_URL}?address=${encodeURIComponent(parsedResult.location)}`);
            if (geoResponse.ok) {
              const geoData = await geoResponse.json();
              if (geoData.lat && geoData.lng) {
                const lat = parseFloat(Number(geoData.lat).toFixed(4));
                const lng = parseFloat(Number(geoData.lng).toFixed(4));
                parsedResult.coordinates = { lat, lng };
                const h3 = getH3Index(lat, lng);
                parsedResult.h3_index = h3;
                updateSpatialCache(h3, parsedResult.location, lat, lng);
              }
            }
          }
        } catch (geoError: any) {
          console.warn("[Geocoding] Servicio local no disponible:", geoError.message);
        }
      }

      // Save anchor
      try {
        const anchorId = generateAnchorId(name);
        insertAnchor({
          id: anchorId,
          location: parsedResult.location,
          latitude: parsedResult.coordinates?.lat,
          longitude: parsedResult.coordinates?.lng,
          is_travel_document: parsedResult.isTravelDocument,
          h3_index: parsedResult.h3_index,
          raw_json: JSON.stringify(parsedResult),
        });
      } catch (dbErr: any) {
        console.warn("[DB] Error registrando anchor en /api/analyze-local:", dbErr.message);
      }

      return res.json(parsedResult);
    } else {
      throw new Error(serviceResponse.error || "El servicio local no pudo extraer información del voucher.");
    }

  } catch (error: any) {
    console.error("Error analyzing local document:", error);
    const isConnectionError = error.message?.includes("fetch") || error.message?.includes("ECONNREFUSED") || error.message?.includes("LOCAL_SERVICE_UNAVAILABLE");
    if (isConnectionError) {
      return res.status(503).json({
        error: "Servicio local de escaneo no disponible",
        details: `No se pudo conectar con el servidor local de escaneo (${LOCAL_VOUCHER_SERVICE}). Asegúrate de que Uvicorn esté iniciado.`,
        code: "LOCAL_SERVICE_UNAVAILABLE",
      });
    }
    res.status(500).json({
      error: "Error en el análisis de documento",
      details: error.message || "Error desconocido al procesar el archivo con el servicio local.",
    });
  }
});

// Chat with itinerary context
app.post("/api/chat-itinerary", async (req, res) => {
  try {
    const { messages, bookings } = req.body;
    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: "Missing or invalid 'messages' array" });
    }

    const formattedBookings = JSON.stringify(bookings || [], null, 2);
    const systemInstruction = `Eres un asistente de viajes personal, inteligente, empático y experto. 
Ayudas al usuario a organizar y responder preguntas sobre sus reservas de viaje (vuelos, hoteles, alquiler de autos y tickets de actividades).

A continuación, tienes la lista estructurada de reservas confirmadas que hemos escaneado de su cuenta de Google Drive:
${formattedBookings}

Por favor, utiliza esta lista para responder a las preguntas del usuario de forma precisa y servicial en español. 
- Si el usuario te pregunta por los costos de los hoteles, vuelos o total de gastos, haz las cuentas matemáticas necesarias.
- Si te pregunta por fechas, horas, ubicaciones o detalles de aerolíneas, extrae las fechas y horarios de los datos provistos.
- Mantén tus respuestas conversacionales, claras y concisas. Evita responder con terminología técnica innecesaria.
- Si no hay datos disponibles en la lista para responder a una pregunta en particular, indícalo amablemente sin inventar datos.`;

    // Map client messages to Gemini content format
    const contents = messages.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'model',
      parts: [{ text: msg.content }]
    }));

    // Call Gemini with resilient retry mechanism
    const response = await generateContentWithRetry({
      model: process.env.GEMINI_MODEL || "gemini-2.5-flash",
      contents: contents,
      config: {
        systemInstruction: systemInstruction,
        temperature: 0.7,
      }
    });

    return res.json({ response: response.text });

  } catch (error: any) {
    console.error("Error in chat itinerary:", error);
    const formatted = formatGeminiError(error);
    res.status(500).json(formatted);
  }
});

// Batch analyze endpoint — proxies each file to local voucher service
app.post("/api/batch-analyze", async (req, res) => {
  try {
    const { files, concurrency } = req.body;
    if (!files || !Array.isArray(files) || files.length === 0) {
      return res.status(400).json({ error: "Missing or empty 'files' array" });
    }

    console.log(`[Batch/Local] Iniciando lote de ${files.length} documentos`);

    const isHealthy = await checkLocalServiceHealth();
    if (!isHealthy) {
      return res.status(503).json({
        error: "Servicio local de escaneo no disponible",
        details: `No se pudo conectar con el servidor local de escaneo (${LOCAL_VOUCHER_SERVICE}). Asegúrate de que Uvicorn esté iniciado.`,
        code: "LOCAL_SERVICE_UNAVAILABLE",
      });
    }

    const results: any[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      console.log(`[Batch/Local] Procesando ${i + 1}/${files.length}: "${file.name}"`);
      try {
        let fileBuffer: Buffer;
        if (file.base64Data) {
          fileBuffer = Buffer.from(file.base64Data, 'base64');
        } else if (file.fileBuffer) {
          fileBuffer = Buffer.from(file.fileBuffer);
        } else {
          throw new Error("No file content provided (base64Data or fileBuffer required)");
        }

        const isPdf = file.mimeType === 'application/pdf' || (file.name || '').toLowerCase().endsWith('.pdf');
        if (isPdf) {
          const pdfResult = await processPdfDocument(fileBuffer, file.name);
          results.push({ file: file.name, success: true, ...pdfResult });
          continue;
        }

        const serviceResponse = await callLocalVoucherService(fileBuffer, file.name, file.mimeType);
        if (serviceResponse.status === "success" && serviceResponse.voucher) {
          const parsed = mapVoucherToBooking(serviceResponse.voucher, file.name);
          results.push({ file: file.name, success: true, ...parsed });
        } else {
          results.push({ file: file.name, success: false, error: serviceResponse.error || "Extraction failed" });
        }
      } catch (err: any) {
        results.push({ file: file.name, success: false, error: err.message });
      }
    }

    const succeeded = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    return res.json({
      total: files.length,
      succeeded,
      failed,
      travelDocuments: succeeded,
      results,
    });
  } catch (error: any) {
    console.error("Error in batch analyze:", error);
    const isConnectionError = error.message?.includes("fetch") || error.message?.includes("ECONNREFUSED");
    if (isConnectionError) {
      return res.status(503).json({
        error: "Servicio local de escaneo no disponible",
        details: `No se pudo conectar con el servidor local de escaneo (${LOCAL_VOUCHER_SERVICE}). Asegúrate de que Uvicorn esté iniciado.`,
        code: "LOCAL_SERVICE_UNAVAILABLE",
      });
    }
    res.status(500).json({ error: "Error en análisis por lotes", details: error.message });
  }
});

// Vite middleware and static files
let httpServer: any = null;

async function startServer() {
  await initDatabase();
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  httpServer = app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on port ${PORT}`);
    exec('start http://localhost:3000');
  });
}

// Graceful shutdown handler
function shutdown(signal: string) {
  console.log(`\n[shutdown] Received ${signal}. Cerrando servidor...`);

  // Stop accepting new connections
  if (httpServer) {
    httpServer.close(() => {
      console.log("[shutdown] Puerto 3000 liberado");
    });
  }

  // Persist and close SQLite
  closeDatabase();

  // Force exit after 3s if something is stuck
  setTimeout(() => {
    console.log("[shutdown] Forzando salida");
    process.exit(0);
  }, 3000);
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

startServer();
