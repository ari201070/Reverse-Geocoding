// api/find-poi.js
import { latLngToCell } from 'h3-js';
import { parseExif, calculateHaversineDistance, calculateCosineSimilarity } from '../lib/geo.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  try {
    const { current_photo, prev_anchor, next_anchor } = req.body;
    
    const MAX_FEASIBLE_SPEED = 25.0; // km/h estricto para Roma Centro
    const H3_RESOLUTION = 9;

    let resolved_lat = current_photo.lat;
    let resolved_lng = current_photo.lng;
    let method = 'direct_exif';

    // 1. OBTENCIÓN DE VECTORES DINOv2 EN CALIENTE (PUENTE LOCAL)
    let visual_bias_ratio = null;
    try {
      const serverResponse = await fetch('http://127.0.0', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_path: current_photo.name })
      });
      
      if (serverResponse.status === 200) {
        const { embedding } = await serverResponse.json();
        
        if (embedding && prev_anchor?.embedding && next_anchor?.embedding) {
          const sim_to_prev = calculateCosineSimilarity(embedding, prev_anchor.embedding);
          const sim_to_next = calculateCosineSimilarity(embedding, next_anchor.embedding);
          
          if (sim_to_prev > 0.60 || sim_to_next > 0.60) {
            visual_bias_ratio = sim_to_next / (sim_to_prev + sim_to_next);
          }
        }
      }
    } catch (err) {
      console.log("⚠️ Servidor DINOv2 offline, continuando por interpolación temporal pura.");
    }

    // 2. INTERPOLACIÓN ESPACIO-TEMPORAL CON PARSING EXIF CORREGIDO
    if ((!resolved_lat || !resolved_lng) && prev_anchor && next_anchor && current_photo.date_taken) {
      const t_prev = parseExif(prev_anchor.date_taken);
      const t_next = parseExif(next_anchor.date_taken);
      const t_curr = parseExif(current_photo.date_taken);

      if (t_prev && t_next && t_curr) {
        const total_duration = t_next - t_prev;
        const current_duration = t_curr - t_prev;

        if (total_duration > 0 && current_duration >= 0) {
          const temporal_ratio = current_duration / total_duration;
          
          const final_ratio = visual_bias_ratio !== null 
            ? (temporal_ratio * 0.4 + visual_bias_ratio * 0.6) 
            : temporal_ratio;

          resolved_lat = prev_anchor.lat + (next_anchor.lat - prev_anchor.lat) * final_ratio;
          resolved_lng = prev_anchor.lng + (next_anchor.lng - prev_anchor.lng) * final_ratio;
          method = visual_bias_ratio !== null ? 'hybrid_dinov2_temporal_roma' : 'temporal_interpolation_roma';
        }
      }
    }

    // 3. SEGURO DE CENTROIDE URBANO
    if (!resolved_lat || !resolved_lng) {
      if (prev_anchor && next_anchor) {
        resolved_lat = (prev_anchor.lat + next_anchor.lat) / 2;
        resolved_lng = (prev_anchor.lng + next_anchor.lng) / 2;
        method = 'neighborhood_centroid_roma_fallback';
      } else {
        return res.status(422).json({ error: 'Falta de datos geométricos en el Forum Boarium' });
      }
    }

    resolved_lat = parseFloat(resolved_lat.toFixed(4));
    resolved_lng = parseFloat(resolved_lng.toFixed(4));

    // 4. DOBLE VETO CINEMÁTICO BLINDADO PEATONAL (PREV Y NEXT)
    if (current_photo.date_taken) {
      const t_curr = parseExif(current_photo.date_taken);
      
      if (prev_anchor) {
        const hours = Math.abs(t_curr - parseExif(prev_anchor.date_taken)) / (1000 * 60 * 60);
        if (hours > 0 && (calculateHaversineDistance(prev_anchor.lat, prev_anchor.lng, resolved_lat, resolved_lng) / hours) > MAX_FEASIBLE_SPEED) {
          return res.status(400).json({ status: 'failed_velocity_veto', reason: 'Salto peatonal imposible en Roma Centro' });
        }
      }
    }

    const h3_index = latLngToCell(resolved_lat, resolved_lng, H3_RESOLUTION);

    return res.status(200).json({
      status: 'resolved',
      meta: { photo_name: current_photo.name, method: method },
      spatial_cache: {
        latitude: resolved_lat,
        longitude: resolved_lng,
        h3_index: h3_index,
        place_name: "Zona Histórica Forum Boarium / Roma"
      }
    });

  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}
