// api/config.js — Exposes safe client-side config (no keys exposed)
export default async (req, res) => {
  if (req.method && req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  return res.status(200).json({
    disablePaidGoogleApis: true,
    nodeEnv: process.env.NODE_ENV || 'development'
  });
};
