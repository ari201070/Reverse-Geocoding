import 'dotenv/config';

const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const DEFAULT_MODEL = process.env.OLLAMA_DEFAULT_MODEL || 'qwen2.5-coder:7b';
const VISION_MODEL = process.env.OLLAMA_VISION_MODEL || 'qwen2.5vl';

function resolveModel(model, hasImages) {
  if (model) return model;
  if (hasImages && VISION_MODEL) return VISION_MODEL;
  return DEFAULT_MODEL;
}

function parseBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks).toString()));
    req.on('error', () => resolve(''));
  });
}

/**
 * Corrige la respuesta de /api/show de Ollama.
 * Algunos modelos (como qwen2.5-coder) devuelven context_length anidado
 * en model_info.qwen2.context_length en vez de context_length al nivel raíz.
 * OpenCode espera context_length en el nivel raíz.
 */
function fixContextLength(body) {
  try {
    const data = typeof body === 'string' ? JSON.parse(body) : body;

    if (data.model_info && typeof data.model_info === 'object') {
      // model_info tiene keys planas como "qwen2.context_length": 32768
      for (const [key, value] of Object.entries(data.model_info)) {
        if (key.endsWith('.context_length') && typeof value === 'number') {
          data.context_length = value;
          console.log(`[api/ollama] Fixed context_length: ${value}`);
        }
      }
    }

    return JSON.stringify(data);
  } catch (e) {
    console.error('[api/ollama] Error fixing context_length:', e.message);
    return body;
  }
}

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const basePath = '/api/ollama';

  // GET /api/ollama → Listar modelos
  if (req.method === 'GET' && url.pathname === basePath) {
    try {
      const tagsRes = await fetch(`${OLLAMA_BASE_URL}/api/tags`);
      const tagsData = await tagsRes.json();
      return res.status(200).json(tagsData);
    } catch (err) {
      return res.status(500).json({ error: `Failed to list models: ${err.message}` });
    }
  }

  // POST /api/ollama → Generate (el frontend llama así con model, prompt, images)
  if (req.method === 'POST' && url.pathname === basePath) {
    try {
      const raw = await parseBody(req);
      let body = {};
      try { body = JSON.parse(raw); } catch { body = {}; }

      const hasImages = !!(body.images && body.images.length > 0);
      const resolvedModel = resolveModel(body.model, hasImages);

      console.log(`[api/ollama] Generate: model=${resolvedModel}, images=${hasImages}`);

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 120000);

      const resp = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: resolvedModel,
          prompt: body.prompt || '',
          images: body.images || [],
          stream: body.stream || false,
          format: body.format || 'json',
        }),
        signal: controller.signal,
      });

      clearTimeout(timeout);
      const text = await resp.text();
      res.status(resp.status).json(JSON.parse(text));
      return;
    } catch (error) {
      if (error.name === 'AbortError') {
        return res.status(504).json({ error: 'Ollama timeout' });
      }
      return res.status(500).json({ error: error.message });
    }
  }

  // Proxy transparente: /api/ollama/api/generate → /api/generate
  // También maneja /api/ollama/api/show, /api/ollama/api/tags, etc.
  const ollamaPath = url.pathname.replace(basePath, '');
  const ollamaUrl = `${OLLAMA_BASE_URL}${ollamaPath}`;

  console.log(`[api/ollama] Proxy: ${req.method} ${url.pathname} → ${ollamaUrl}`);

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120000);

    let body;
    if (['POST', 'PUT', 'PATCH'].includes(req.method)) {
      body = await parseBody(req);
    }

    const response = await fetch(ollamaUrl, {
      method: req.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: body || undefined,
      signal: controller.signal,
    });

    clearTimeout(timeout);

    const responseBody = await response.text();
    let finalBody = responseBody;

    if (ollamaPath === '/api/show') {
      finalBody = fixContextLength(responseBody);
    }

    const contentType = response.headers.get('content-type') || 'application/json';
    res.writeHead(response.status, { 'Content-Type': contentType });
    res.end(finalBody);

  } catch (error) {
    if (error.name === 'AbortError') {
      res.status(504).json({ error: 'Ollama timeout - CPU is likely congested' });
    } else {
      console.error(`[api/ollama] Proxy Error:`, error.message);
      res.status(500).json({ error: error.message });
    }
  }
}