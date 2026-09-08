// api/analyze-image.js — Free Vision API cascade (Ollama → OpenRouter → Gemini)
// Receives POST { image_base64, lat, lng, timestamp, current_step, mime_type }
// Returns { labels: [string], landmarks: [string], texts: [string], status: string }
import memoryStore from './memory-store.js';

async function callOllamaVision(imageBase64) {
  const disableOllama = process.env.DISABLE_OLLAMA === 'true';
  if (disableOllama) {
    console.log("[analyze-image] Ollama está desactivado en la configuración. Saltando...");
    return null;
  }

  const ollamaUrl = `${process.env.OLLAMA_BASE_URL || 'http://localhost:11434'}/api/generate`;
  const visionModel = process.env.OLLAMA_VISION_MODEL || 'moondream';
  
  console.log(`[analyze-image] Intentando inferencia de visión local con Ollama (${visionModel})...`);
  
  const payload = {
    model: visionModel,
    prompt: `Analyze this photo and act as an expert landmark and OCR detector.
You must return a JSON object with the following fields:
- "labels": Array of strings representing visual descriptors/tags.
- "landmarks": Array of strings representing names of specific landmarks or buildings.
- "texts": Array of strings representing any text, signs, logos visible in the photo (OCR).
Return ONLY the JSON object, with no markdown formatting, no backticks, and no explanation.`,
    images: [imageBase64],
    stream: false,
    format: "json"
  };

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    
    const res = await fetch(ollamaUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      const text = data.response;
      if (text) {
        try {
          const parsed = JSON.parse(text);
          return {
            labels: Array.isArray(parsed.labels) ? parsed.labels : [],
            landmarks: Array.isArray(parsed.landmarks) ? parsed.landmarks : [],
            texts: Array.isArray(parsed.texts) ? parsed.texts : [],
            status: 'SUCCESS_OLLAMA_LOCAL_VISION'
          };
        } catch (jsonErr) {
          console.error("[Ollama Vision Parse Error]:", jsonErr.message, "Raw text:", text);
        }
      }
    } else {
      console.warn(`[Ollama Vision API Warn]: Status ${res.status}`);
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      console.warn("[Ollama Vision Timeout]: La inferencia local de Ollama tardó demasiado.");
    } else {
      console.warn("[Ollama Vision Exception]:", e.message);
    }
  }
  return null;
}

async function callOpenRouterVision(imageBase64, current_step, mime_type) {
  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (!openRouterKey) {
    console.log("[OpenRouter Vision] No API Key configured.");
    return null;
  }

  // 1. SELECCIÓN DINÁMICA DEL MODELO SEGÚN SUS CUALIDADES VISUALES Y EL PASO DEL PIPELINE
  let primaryModel = "google/gemma-4-31b-it:free"; // Fallback omnimodal por defecto

  const isVideo = mime_type && (mime_type.includes('video') || mime_type.includes('mp4') || mime_type.includes('quicktime'));

  if (isVideo) {
    // Gemma 4 maneja clips de video nativos cortos
    primaryModel = "google/gemma-4-31b-it:free";
    console.log(`[OpenRouter Vision] Detectado formato de video. Asignando modelo omnimodal primario: ${primaryModel}`);
  } else if (current_step === 'classification') {
    // Llama 3.2 Vision es veloz y óptimo para pre-clasificación de entornos
    primaryModel = "meta/llama-3.2-11b-vision-instruct:free";
  } else if (current_step === 'ocr_and_landmarks' || current_step === 'extraction' || current_step === '2') {
    // Qwen 2.5 VL es el rey indiscutido del OCR espacial y detección de carteles/hitos
    primaryModel = "qwen/qwen-2.5-vl-72b-instruct:free";
  } else if (current_step === 'micro_fisionomia' || current_step === 'analysis' || current_step === '4') {
    // Pixtral respeta la resolución y relación de aspecto nativa para fisonomía arquitectónica profunda
    primaryModel = "mistralai/pixtral-12b:free";
  }

  // Pool completo de modelos gratuitos de visión ordenados dinámicamente (Primero el especialista del paso actual)
  const basePool = [
    "qwen/qwen-2.5-vl-72b-instruct:free",
    "mistralai/pixtral-12b:free",
    "google/gemma-4-31b-it:free",
    "meta/llama-3.2-11b-vision-instruct:free"
  ];
  
  const models = [primaryModel, ...basePool.filter(m => m !== primaryModel)];

  for (const model of models) {
    console.log(`[analyze-image] Intentando análisis visual en OpenRouter con: ${model} (Paso: ${current_step || 'No especificado'})`);
    try {
      const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${openRouterKey}`,
          'HTTP-Referer': 'http://localhost:3000',
          'X-Title': 'Reverse Geocoding'
        },
        body: JSON.stringify({
          model: model,
          messages: [
            {
              role: 'user',
              content: [
                {
                  type: 'text',
                  text: `Analyze this media asset and act as an expert landmark and OCR detector.
You must return a JSON object with the following fields:
- "labels": Array of strings representing visual descriptors, tags, or fine-grained style/architectural elements.
- "landmarks": Array of strings representing names of specific landmarks, buildings, public spaces, or geographic features.
- "texts": Array of strings representing any text, signs, street names, logos visible in the asset (OCR).
Return ONLY the raw JSON object, with no markdown formatting, no backticks, and no explanation.`
                },
                {
                  type: 'image_url',
                  image_url: {
                    url: `data:${mime_type || 'image/jpeg'};base64,${imageBase64}`
                  }
                }
              ]
            }
          ]
        })
      });

      if (res.ok) {
        const data = await res.json();
        let text = data.choices?.[0]?.message?.content || '';
        
        // Limpieza robusta de bloques de código markdown si el modelo ignora la instrucción estricta
        text = text.replace(/```json/gi, '').replace(/```/g, '').trim();
        
        try {
          const parsed = JSON.parse(text);
          return {
            labels: Array.isArray(parsed.labels) ? parsed.labels : [],
            landmarks: Array.isArray(parsed.landmarks) ? parsed.landmarks : [],
            texts: Array.isArray(parsed.texts) ? parsed.texts : [],
            status: `SUCCESS_OPENROUTER_VISION_${model.replace(/[:\/.-]/g, '_')}`
          };
        } catch (jsonErr) {
          console.error(`[OpenRouter Vision Parse Error para ${model}]:`, jsonErr.message, "Texto crudo recibido:", text);
        }
      } else {
        const errText = await res.text().catch(() => '');
        console.error(`[OpenRouter Vision API Error para ${model}]: Status ${res.status}. Body: ${errText}`);
      }
    } catch (e) {
      console.error(`[OpenRouter Vision Exception para ${model}]:`, e.message);
    }
  }
  return null;
}

async function callGeminiVision(imageBase64, mime_type) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    console.log("[analyze-image] No GEMINI_API_KEY configurada.");
    return null;
  }
  const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
  
  console.log("[analyze-image] Llamando a Gemini 2.5 Flash Multimodal Nativo (Free Tier)...");
  
  const payload = {
    contents: [
      {
        parts: [
          {
            text: `Analyze this photo and act as an expert landmark and OCR detector.
You must return a JSON object with the following fields:
- "labels": Array of strings representing visual descriptors/tags.
- "landmarks": Array of strings representing names of specific landmarks or buildings.
- "texts": Array of strings representing any text, signs, logos visible in the photo (OCR).
Return ONLY the JSON object, with no markdown formatting, no backticks, and no explanation.`
          },
          {
            inlineData: {
              mimeType: mime_type || "image/jpeg",
              data: imageBase64
            }
          }
        ]
      }
    ],
    generationConfig: {
      responseMimeType: "application/json"
    }
  };

  try {
    const res = await fetch(geminiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
      if (text) {
        try {
          const parsed = JSON.parse(text);
          return {
            labels: Array.isArray(parsed.labels) ? parsed.labels : [],
            landmarks: Array.isArray(parsed.landmarks) ? parsed.landmarks : [],
            texts: Array.isArray(parsed.texts) ? parsed.texts : [],
            status: 'SUCCESS_GEMINI_FALLBACK'
          };
        } catch (jsonErr) {
          console.error("[Gemini Vision Parse Error]:", jsonErr.message, "Texto crudo recibido:", text);
        }
      }
    } else {
      const errText = await res.text().catch(() => '');
      console.error(`[Gemini Vision API Error]: Status ${res.status}. Body: ${errText}`);
    }
  } catch (e) {
    console.error("[Gemini Vision Exception]:", e.message);
  }
  return null;
}

async function callFreeVision(imageBase64, current_step, mime_type) {
  // 1. Prioridad 1: Ollama Local (Ahorro total de cuotas externas si está activo y responde a tiempo)
  let result = await callOllamaVision(imageBase64);
  if (result) return result;

  // 2. Prioridad 2: Cascada Especializada de OpenRouter (Llama 3.2, Qwen VL, Pixtral, Gemma 4)
  result = await callOpenRouterVision(imageBase64, current_step, mime_type);
  if (result) return result;

  // 3. Prioridad 3: Gemini API Directo (Último resguardo del Tier gratuito)
  result = await callGeminiVision(imageBase64, mime_type);
  if (result) return result;

  return null;
}

export default async (req, res) => {
  if (req.method && req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Desestructuramos las variables contextuales inyectadas por el pipeline agéntico de OpenCode
  const { image_base64, lat, lng, timestamp, current_step, mime_type } = req.body;
  if (!image_base64) {
    return res.status(400).json({ error: 'image_base64 required' });
  }

  // Intento de bypass mediante caché espacio-temporal primero (Anchor Photos)
  if (lat && lng && timestamp) {
    try {
      const anchor = await memoryStore.findRecentAnchorPhoto(lat, lng, timestamp);
      if (anchor) {
        console.log(`[Vision Bypass] Encontrada foto ancla reciente en DB: ID ${anchor.id}. Saltando llamadas de API externas.`);
        return res.status(200).json({
          labels: [],
          landmarks: [],
          texts: [],
          status: 'BYPASSED_SPATIO_TEMPORAL',
          anchor: {
            lat: anchor.lat,
            lng: anchor.lng,
            timestamp_utc: anchor.timestamp_utc,
            visual_signature: anchor.visual_signature,
            source: 'ANCHOR_PHOTO'
          }
        });
      }
    } catch (dbErr) {
      console.error('[Vision Bypass] Error al verificar la base de datos:', dbErr.message);
    }
  }

  // Ejecución de la cascada inteligente de visión gratuita
  const freeResult = await callFreeVision(image_base64, current_step, mime_type);
  if (freeResult) {
    if (lat && lng && timestamp) {
      try {
        await memoryStore.saveAnchorPhoto(lat, lng, timestamp, {
          labels: freeResult.labels,
          landmarks: freeResult.landmarks,
          texts: freeResult.texts
        });
        console.log(`[Free Vision Anchor] Foto ancla guardada exitosamente en la base de datos.`);
      } catch (saveErr) {
        console.error('[Free Vision Anchor] Error al persistir la foto ancla:', saveErr.message);
      }
    }
    return res.status(200).json(freeResult);
  }

  return res.status(200).json({
    labels: [],
    landmarks: [],
    texts: [],
    status: 'SKIPPED',
    error: 'No free vision LLM available'
  });
};