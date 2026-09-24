// api/find-poi.js
import { latLngToCell } from 'h3-js';
import { z } from 'zod';
import { parseExif, calculateHaversineDistance, calculateCosineSimilarity } from '../lib/geo.js';

const anchorSchema = z.object({
  name: z.string(),
  date_taken: z.string(),
  lat: z.number(),
  lng: z.number(),
  embedding: z.array(z.number()).optional()
});

const requestBodySchema = z.object({
  current_photo: z.object({
    name: z.string(),
    date_taken: z.string().nullable().optional(),
    lat: z.number().nullable().optional(),
    lng: z.number().nullable().optional()
  }),
  prev_anchor: anchorSchema.nullable().optional(),
  next_anchor: anchorSchema.nullable().optional(),
  visual_embedding: z.array(z.number()).optional(),
  options: z.object({
    max_speed: z.number().optional().default(120.0),
    h3_res: z.number().optional().default(9)
  }).optional().default({})
});

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método no permitido' });
  }
  const result = requestBodySchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ error: 'Payload inválido', details: result.error.errors });
  }
  try {
    const { current_photo, prev_anchor, next_anchor, visual_embedding, options } = result.data;
    const MAX_FEASIBLE_SPEED = options.max_speed;
    const H3_RESOLUTION = options.h3_res;
    let resolved_lat = current_photo.lat || null;
    let resolved_lng = current_photo.lng || null;
    let method = 'direct_exif';
    let visual_bias_ratio = null;
    if (visual_embedding && prev_anchor?.embedding && next_anchor?.embedding) {
      const sim_to_prev = calculateCosineSimilarity(visual_embedding, prev_anchor.embedding);
      const sim_to_next = calculateCosineSimilarity(visual_embedding, next_anchor.embedding);
      if (sim_to_prev > 0.60 || sim_to_next > 0.60) {
        visual_bias_ratio = sim_to_next / (sim_to_prev + sim_to_next);
      }
    }
    if ((!resolved_lat || !resolved_lng) && prev_anchor && next_anchor && current_photo.date_taken) {
      const t_prev = parseExif(prev_anchor.date_taken);
      const t_next = parseExif(next_anchor.date_taken);
      const t_curr = parseExif(current_photo.date_taken);
      if (t_prev && t_next && t_curr && !isNaN(t_prev) && !isNaN(t_next) && !isNaN(t_curr)) {
        const total_duration = t_next - t_prev;
        const current_duration = t_curr - t_prev;
        if (total_duration > 0 && current_duration >= 0) {
          const temporal_ratio = current_duration / total_duration;
          const final_ratio = visual_bias_ratio !== null ? (temporal_ratio * 0.4 + visual_bias_ratio * 0.6) : temporal_ratio;
          resolved_lat = prev_anchor.lat + (next_anchor.lat - prev_anchor.lat) * final_ratio;
          resolved_lng = prev_anchor.lng + (next_anchor.lng - prev_anchor.lng) * final_ratio;
          method = visual_bias_ratio !== null ? 'hybrid_dinov2_temporal_m17' : 'temporal_interpolation_m17';
        }
      }
    }
    if (!resolved_lat || !resolved_lng) {
      if (prev_anchor && next_anchor) {
        resolved_lat = (prev_anchor.lat + next_anchor.lat) / 2;
        resolved_lng = (prev_anchor.lng + next_anchor.lng) / 2;
        method = 'neighborhood_centroid_fallback';
      } else {
        return res.status(422).json({ status: 'rejected', reason: 'No hay suficientes datos espaciales ni anclas para interpolar la trayectoria.' });
      }
    }
    resolved_lat = parseFloat(resolved_lat.toFixed(4));
    resolved_lng = parseFloat(resolved_lng.toFixed(4));
    if (current_photo.date_taken) {
      const t_curr = parseExif(current_photo.date_taken);
      if (t_curr && !isNaN(t_curr)) {
        if (prev_anchor) {
          const t_prev = parseExif(prev_anchor.date_taken);
          const hours_prev = Math.abs(t_curr - t_prev) / (1000 * 60 * 60);
          if (hours_prev > 0) {
            const dist_prev = calculateHaversineDistance(prev_anchor.lat, prev_anchor.lng, resolved_lat, resolved_lng);
            const speed_prev = dist_prev / hours_prev;
            if (speed_prev > MAX_FEASIBLE_SPEED) {
              return res.status(400).json({ status: 'failed_velocity_veto', segment: 'prev_to_current', required_speed_kmh: parseFloat(speed_prev.toFixed(2)), reason: `Velocidad imposible detectada en segmento origen-foto (${speed_prev.toFixed(2)} km/h)` });
            }
          }
        }
        if (next_anchor) {
          const t_next = parseExif(next_anchor.date_taken);
          const hours_next = Math.abs(t_next - t_curr) / (1000 * 60 * 60);
          if (hours_next > 0) {
            const dist_next = calculateHaversineDistance(resolved_lat, resolved_lng, next_anchor.lat, next_anchor.lng);
            const speed_next = dist_next / hours_next;
            if (speed_next > MAX_FEASIBLE_SPEED) {
              return res.status(400).json({ status: 'failed_velocity_veto', segment: 'current_to_next', required_speed_kmh: parseFloat(speed_next.toFixed(2)), reason: `Velocidad imposible detectada en segmento foto-destino (${speed_next.toFixed(2)} km/h)` });
            }
          }
        }
      }
    }
    let h3_index = null;
    try {
      h3_index = latLngToCell(resolved_lat, resolved_lng, H3_RESOLUTION);
    } catch (h3Error) {
      return res.status(500).json({ error: 'Error al calcular el índice H3 espacial', details: h3Error.message });
    }
    const latRef = resolved_lat >= 0 ? 'N' : 'S';
    const lngRef = resolved_lng >= 0 ? 'E' : 'W';
    const clean_date = current_photo.date_taken || prev_anchor?.date_taken || "2023:04:29 12:40:00";
    return res.status(200).json({
      status: 'resolved',
      meta: { photo_name: current_photo.name, method: method, tags: ["viaje_bosnia_2023"] },
      spatial_cache: { latitude: resolved_lat, longitude: resolved_lng, lat: resolved_lat, lng: resolved_lng, h3_index: h3_index, place_name: method.includes('m17') ? "Ruta M17 Konjic-Sarajevo / Bosnia" : "Área de Influencia Conectividad M17" },
      spatial_data: { latitude: resolved_lat, longitude: resolved_lng, lat: resolved_lat, lng: resolved_lng, h3_index: h3_index, place_name: method.includes('m17') ? "Ruta M17 Konjic-Sarajevo / Bosnia" : "Área de Influencia Conectividad M17" },
      trigger_physical_write: { exec_exiftool: true, command: `exiftool -GPSLatitude=${Math.abs(resolved_lat)} -GPSLatitudeRef=${latRef} -GPSLongitude=${Math.abs(resolved_lng)} -GPSLongitudeRef=${lngRef} -GPSVersionID="2.3.0.0" -ImageDescription="Resuelta via ${method}" -DateTimeOriginal="${clean_date}" -overwrite_original "${current_photo.name}"` }
    });
  } catch (error) {
    return res.status(500).json({ error: 'Error interno en la ejecución del pipeline', details: error.message });
  }
}
