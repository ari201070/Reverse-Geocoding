// api/analyze-image.js - Cloud Vision API integration (CommonJS for Vercel consistency)
// Receives POST { image_base64 }
// Returns { labels: [string], landmarks: [string], texts: [string] }

module.exports = async (req, res) => {
  if (req.method && req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { image_base64 } = req.body;
  if (!image_base64) {
    return res.status(400).json({ error: 'image_base64 required' });
  }

  const apiKey = process.env.GOOGLE_MAPS_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'API Key not configured' });
  }

  try {
    const visionUrl = `https://vision.googleapis.com/v1/images:annotate?key=${apiKey}`;
    const payload = {
      requests: [
        {
          image: { content: image_base64 },
          features: [
            { type: 'LABEL_DETECTION', maxResults: 15 },
            { type: 'LANDMARK_DETECTION', maxResults: 5 },
            { type: 'TEXT_DETECTION', maxResults: 5 }
          ]
        }
      ]
    };

    const visionRes = await fetch(visionUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!visionRes.ok) {
      const errorText = await visionRes.text();
      throw new Error(`Vision API error (${visionRes.status}): ${errorText}`);
    }

    const data = await visionRes.json();
    if (data.responses?.[0]?.error) {
      throw new Error(`Vision API Logic Error: ${data.responses[0].error.message}`);
    }

    const res0 = data.responses[0];
    const labels    = (res0.labelAnnotations    || []).map(a => a.description);
    const landmarks = (res0.landmarkAnnotations || []).map(a => a.description);
    const texts     = (res0.textAnnotations     || []).map(a => a.description);

    return res.status(200).json({ labels, landmarks, texts });
  } catch (err) {
    console.error('analyze-image error:', err);
    return res.status(500).json({ error: err.message || String(err) });
  }
};
