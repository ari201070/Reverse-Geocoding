import { query } from '../lib/pg_db.js';
import { calculateAzimuth, calculateHeadingDelta } from '../lib/geo.js';
import { z } from 'zod';

// Guardrail de Validación para los payloads entrantes del pipeline de Roma
const requestPayloadSchema = z.object({
  photo_name: z.string().min(1),
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  camera_heading: z.number().min(0).max(360).nullable().optional(),
  // Embedding generado del lado del servidor (ej. dinov2-base)
  embedding: z.array(z.number()).optional()
});

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método no permitido' });
  }

  try {
    // 1. Control de Puerta con Zod (Validación estricta de entrada)
    const parsedData = requestPayloadSchema.parse(req.body);
    const { latitude, longitude, camera_heading, embedding } = parsedData;

    console.log(`📡 [API /find-poi] Evaluando foto: ${parsedData.photo_name} (Heading: ${camera_heading ?? 'N/A'})`);

    // 2. Query Espacial PostGIS (Capa 2 y 3: Filtro radial GiST + Búsqueda Vectorial HNSW)
    // Selección explícita según presencia de embedding - elimina .replace() encadenados
    const sql = embedding
      ? `SELECT id, name, category, ST_X(geom) as longitude, ST_Y(geom) as latitude, camera_heading,
                1 - (embedding <=> $1::vector) AS vector_similarity 
         FROM spatial_cache 
         WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint($2,$3),4326)::geography, 500) 
         ORDER BY vector_similarity DESC LIMIT 10`
      : `SELECT id, name, category, ST_X(geom) as longitude, ST_Y(geom) as latitude, camera_heading,
                1.0 AS vector_similarity 
         FROM spatial_cache 
         WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint($1,$2),4326)::geography, 500) 
         ORDER BY vector_similarity DESC LIMIT 10`;

    const dbParams = embedding ? [JSON.stringify(embedding), longitude, latitude] : [longitude, latitude];

    const { rows: candidates } = await query(sql, dbParams);

    // 3. CAPA DE DESEMPATE ANGULAR: Filtrado y Scoring por Cono de Visión
    const processedPois = candidates.map(poi => {
      // Calcular azimut matemático desde la foto hacia el POI
      const azimuthToPoi = calculateAzimuth(latitude, longitude, poi.latitude, poi.longitude);
      
      // Calcular desviación respecto a la brújula del teléfono
      const headingDelta = calculateHeadingDelta(camera_heading, azimuthToPoi);

      // Calculamos un factor multiplicador para el Score de Confianza final
      let directionalBonus = 1.0;
      let isInCone = true;

      if (headingDelta !== null) {
        // Guardrail estricto: Si cae fuera del cono frontal de 30°, penalizamos el score
        if (headingDelta > 30.0) {
          isInCone = false;
          directionalBonus = 0.4; // Penalización drástica por desalineación de cámara
        } else {
          // Bonus progresivo: Mientras más cerca de 0° (frontal), mayor el multiplicador (hasta 1.3)
          directionalBonus = 1.3 - (headingDelta / 100);
        }
      }

      // Score de confianza híbrido consolidado
      const finalConfidenceScore = poi.vector_similarity * directionalBonus;

      return {
        ...poi,
        azimuth_to_poi: parseFloat(azimuthToPoi.toFixed(2)),
        heading_delta: headingDelta !== null ? parseFloat(headingDelta.toFixed(2)) : null,
        is_in_cone: isInCone,
        confidence_score: parseFloat(finalConfidenceScore.toFixed(4))
      };
    });

    // 4. Ordenar los resultados por el score híbrido (Vector + Cono de Visión)
    processedPois.sort((a, b) => b.confidence_score - a.confidence_score);

    return res.status(200).json({
      success: true,
      photo_evaluated: parsedData.photo_name,
      camera_heading_reported: camera_heading ?? null,
      results: processedPois
    });

  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ success: false, error: 'Payload inválido', details: error.errors });
    }
    console.error('❌ Error en el handler de find-poi:', error);
    return res.status(500).json({ success: false, error: 'Internal Server Error' });
  }
}
