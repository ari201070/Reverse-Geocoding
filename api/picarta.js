// api/picarta.js
// Proxy backend para Picarta AI para proteger el token
// Recibe POST { image_base64 }
// Retorna la geolocalización estimada de la IA

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const { image_base64 } = req.body;
  if (!image_base64) {
    res.status(400).json({ error: 'image_base64 required' });
    return;
  }

  const token = process.env.VITE_PICARTA_API_TOKEN;
  
  if (!token) {
    res.status(500).json({ error: 'Picarta API Token not configured in server' });
    return;
  }

  try {
    const picartaUrl = "https://picarta.ai/classify";
    const payload = {
      TOKEN: token,
      IMAGE: image_base64,
      TOP_K: 1
    };

    const picartaRes = await fetch(picartaUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!picartaRes.ok) {
      const errorText = await picartaRes.text();
      throw new Error(`Picarta API error (${picartaRes.status}): ${errorText}`);
    }

    const data = await picartaRes.json();
    
    // Normalizar la respuesta para el frontend
    if (data && (data.ai_lat !== undefined) && (data.ai_lon !== undefined)) {
      res.status(200).json({
        lat: data.ai_lat,
        lng: data.ai_lon,
        city: data.city || '',
        country: data.country || '',
        source: 'picarta'
      });
    } else {
      res.status(200).json({ error: 'No localization found', detail: data });
    }
  } catch (err) {
    console.error('picarta-proxy error', err);
    res.status(500).json({ error: err.message || String(err) });
  }
}
