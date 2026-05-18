// api/config.js - Exposes safe client-side keys (ESM)
export default async (req, res) => {
  if (req.method && req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  // Do NOT expose the raw Maps key to the frontend.
  // Return only a presence flag so the client knows whether a key is configured.
  return res.status(200).json({
    googleMapsKeyPresent: !!process.env.GOOGLE_MAPS_API_KEY,
    nodeEnv: process.env.NODE_ENV || 'development'
  });
};
