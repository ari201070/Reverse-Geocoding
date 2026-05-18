// api/config.js - Exposes safe client-side keys (ESM)
export default async (req, res) => {
  if (req.method && req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Never expose the raw API key to the browser. Frontend may read
  // `googleMapsKeyPresent` to know whether server-side integration is
  // configured; all calls requiring the key should be proxied through
  // server endpoints.
  const key = process.env.GOOGLE_MAPS_API_KEY || '';
  // Only expose the key in non-production when explicitly allowed via
  // DEV_EXPOSE_KEY=true. This prevents accidental leakage but allows
  // local testing when the developer opts in.
  const exposeKey = (process.env.NODE_ENV || 'development') !== 'production' && process.env.DEV_EXPOSE_KEY === 'true';

  return res.status(200).json({
    googleMapsApiKey: exposeKey ? key : '',
    // boolean flag so frontend can know whether backend has a key configured
    googleMapsKeyPresent: !!key,
    nodeEnv: process.env.NODE_ENV || 'development'
  });
};
