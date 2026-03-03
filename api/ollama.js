export default async function handler(req, res) {
  console.log(`[api/ollama] ${req.method} request received`);
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method Not Allowed' });
  }

  const { model, prompt, images, stream } = req.body;

  try {
    // Definimos un timeout para evitar que la función se quede colgada
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 25000); // 25s timeout

    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: model || 'phi3',
        prompt: prompt,
        images: images || [],
        stream: stream || false,
        format: 'json'
      }),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errorText = await response.text();
      return res.status(response.status).json({ error: `Ollama API error: ${errorText}` });
    }

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    if (error.name === 'AbortError') {
      return res.status(504).json({ error: 'Ollama timeout - CPU is likely congested' });
    }
    console.error('Ollama Proxy Error:', error);
    res.status(500).json({ error: error.message });
  }
}
