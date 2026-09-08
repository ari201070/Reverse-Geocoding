/**
 * api/geoapify-handler.js
 * 
 * New Module for Geoapify Reverse Geocoding API integration.
 * Provides 3,000 free requests per day (Zero-OPEX tier fallback).
 * Documentation: https://www.geoapify.com/reverse-geocoding-api/
 */

import fetch from 'node-fetch';

/**
 * Reverse Geocodes coordinates using Geoapify
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {string} apiKey - Geoapify API Key
 * @returns {Promise<Object>} Normalized location data
 */
export async function reverseGeocodeGeoapify(lat, lon, apiKey) {
  if (!apiKey) {
    throw new Error('Geoapify API Key is missing');
  }

  const url = `https://api.geoapify.com/v1/geocode/reverse?lat=${lat}&lon=${lon}&apiKey=${apiKey}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Geoapify API Error: ${errorData.message || response.statusText}`);
    }

    const data = await response.json();
    
    if (!data.features || data.features.length === 0) {
      return null;
    }

    // Normalize response based on our Consensus Engine requirements
    const result = data.features[0].properties;
    
    return {
      source: 'geoapify',
      location_name: result.name || result.address_line1 || 'Unknown POI',
      address: result.formatted || '',
      city: result.city || result.municipality || '',
      country: result.country || '',
      country_code: result.country_code || '',
      postcode: result.postcode || '',
      confidence: result.rank?.confidence || 0,
      raw: result // Keep raw data for advanced debugging if needed
    };
  } catch (error) {
    console.error('Geoapify Handler Error:', error.message);
    throw error;
  }
}

/**
 * Standard API Route handler (optional usage via HTTP)
 */
export default async (req, res) => {
  const { lat, lon } = req.query;
  const apiKey = process.env.GEOAPIFY_API_KEY;

  if (!lat || !lon) {
    return res.status(400).json({ error: 'Latitude and Longitude are required' });
  }

  try {
    const result = await reverseGeocodeGeoapify(parseFloat(lat), parseFloat(lon), apiKey);
    return res.status(200).json(result);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
};
