// api/config.js - Exposes safe client-side keys (CommonJS)
module.exports = async (req, res) => {
  if (req.method && req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  // Only expose the Maps key (restrict it by domain in Google Cloud Console)
  return res.status(200).json({
    googleMapsApiKey: process.env.GOOGLE_MAPS_API_KEY || ''
  });
};
