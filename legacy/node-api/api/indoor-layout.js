/**
 * api/indoor-layout.js
 * Sovereign $0 FOSS Backend Endpoint for Indoor Floor Plans
 * Uses H3 Resolution 9 Index for Spatial Clustering & Persists data locally.
 */

import fs from 'fs';
import path from 'path';
import * as h3 from 'h3-js';

const CACHE_FILE = path.join(process.cwd(), '.data', 'indoor_floorplans.json');

// Ensure directory and file exist
function ensureCacheExists() {
  const dir = path.dirname(CACHE_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  if (!fs.existsSync(CACHE_FILE)) {
    fs.writeFileSync(CACHE_FILE, JSON.stringify({}));
  }
}

export default async function handler(req, res) {
  ensureCacheExists();

  if (req.method === 'GET') {
    const lat = parseFloat(req.query.lat);
    const lng = parseFloat(req.query.lng);

    if (isNaN(lat) || isNaN(lng)) {
      return res.status(400).json({ error: "Missing or invalid lat/lng parameters" });
    }

    try {
      const h3Index = h3.latLngToCell(lat, lng, 9);
      const data = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
      const features = data[h3Index] || [];
      
      console.log(`[Indoor Layout] Retrieved ${features.length} custom rooms for H3: ${h3Index}`);
      return res.status(200).json({ h3Index, features });
    } catch (err) {
      return res.status(500).json({ error: "Failed to read indoor layouts: " + err.message });
    }
  }

  if (req.method === 'POST') {
    const { lat, lng, feature } = req.body;

    if (lat === undefined || lng === undefined || !feature) {
      return res.status(400).json({ error: "Missing lat, lng or feature in body" });
    }

    try {
      const h3Index = h3.latLngToCell(parseFloat(lat), parseFloat(lng), 9);
      const data = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
      
      if (!data[h3Index]) {
        data[h3Index] = [];
      }
      
      // Store level inside properties if not present
      if (feature.properties) {
        feature.properties.h3Index = h3Index;
      }

      data[h3Index].push(feature);
      fs.writeFileSync(CACHE_FILE, JSON.stringify(data, null, 2));
      
      console.log(`[Indoor Layout] Persisted custom room "${feature.properties?.name}" under H3: ${h3Index}`);
      return res.status(200).json({ success: true, h3Index, features: data[h3Index] });
    } catch (err) {
      return res.status(500).json({ error: "Failed to save indoor layout: " + err.message });
    }
  }

  return res.status(405).json({ error: "Method not allowed" });
}
