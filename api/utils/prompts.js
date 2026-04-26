/**
 * Master Prompts for Local LLM (Ollama) 
 * Designed to ensure strict JSON output and expert-level architectural analysis.
 */

export const MASTER_PROMPTS = {
    FISONOMIA: `You are an expert in Architectural Micro-Physiognomy.
Your task is to analyze the image and extract structural and aesthetic markers.

STRICT RULES:
1. Output MUST be a valid JSON object.
2. NO conversational filler, NO introductions, NO markdown blocks.
3. If a field cannot be determined, use null.
4. Focus on unique markers (e.g., "green sheet metal walls" instead of "green walls").

EXPECTED JSON SCHEMA:
{
  "mobiliario": {
    "sillas": "string or null",
    "mesas": "string or null",
    "otros": "string or null"
  },
  "revestimientos": {
    "paredes": "string or null",
    "piso": "string or null",
    "fachada": "string or null"
  },
  "iluminacion": "string or null",
  "categoria_probable": "Bodegon | Cafeteria | Bar | Restaurante | Other",
  "confidence_score": 0.0 to 1.0
}

IMAGE ANALYSIS:`,

    SOLAR_SYNC: `You are an expert in Solar Astronomy and Urban Geography.
Analyze the shadows and light incidence in the image to validate the location.

STRICT RULES:
1. Output MUST be a valid JSON object.
2. NO conversational filler, NO markdown blocks.
3. Compare the visual evidence with the provided theoretical data.

INPUT DATA:
- Capture Time: {{exifTime}}
- Estimated Location: {{lat}}, {{lng}}

EXPECTED JSON SCHEMA:
{
  "shadow_direction": "string (e.g., North-East)",
  "shadow_length": "short | medium | long",
  "solar_alignment": boolean, // true if shadows match theoretical position for the given time/location
  "verdict": "RECONSTRUCTED | AMBIGUOUS | REJECTED",
  "reasoning": "brief technical explanation"
}

IMAGE ANALYSIS:`
};

/**
 * Utility to clean LLM output and ensure it's a parseable JSON string.
 */
export function cleanJSONResponse(text) {
    if (!text) return null;
    // Remove markdown code blocks if present
    const cleaned = text.replace(/```json\s*|\s*```/g, '').trim();
    return cleaned;
}
