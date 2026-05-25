// api/resolve-puzzle.js - Agentic Batch Consensus Orchestrator (v5.1 - Industrial Grade)
import 'dotenv/config';
import memoryStore from './memory-store.js';
import findPoiHandler from './find-poi.js';
import { sanitizeString as sanitize, reconcileName, calculateConsensus } from './python-service.js';
import { latLngToCell } from 'h3-js';
import crypto from 'crypto';
import { callModel, tool, createInitialState, buildTurnContext, Agent } from '@openrouter/agent';
import { z } from 'zod';
import { loadSkill, listAvailableSkills } from './utils/skill-loader.js';
import { MASTER_PROMPTS, cleanJSONResponse } from './utils/prompts.js';

const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const H3_RESOLUTION = 9;
const INHERIT_WINDOW_MS = 15 * 60 * 1000;

/**
 * Fallback de coincidencia difusa en JavaScript si el microservicio de Python está inactivo.
 * Calcula una similitud de tokens en base a intersección (Token Set Ratio simplificado).
 */
function calculateFallbackFuzzRatio(s1, s2) {
    if (!s1 || !s2) return 0;
    const clean = (s) => s.toLowerCase().replace(/[^a-z0-9 ]/g, '').split(/\s+/).filter(Boolean);
    const tokens1 = new Set(clean(s1));
    const tokens2 = new Set(clean(s2));
    
    if (tokens1.size === 0 || tokens2.size === 0) return 0;
    
    const intersection = new Set([...tokens1].filter(x => tokens2.has(x)));
    const score = (2.0 * intersection.size) / (tokens1.size + tokens2.size) * 100;
    return Math.round(score);
}

// Custom Agent class to support mock tests, OpenRouter and Ollama local fallback
class Agent {
    constructor(config) {
        this.apiKey = config.apiKey || process.env.OPENROUTER_API_KEY;
        this.model = config.model || 'google/gemini-flash-1.5';
        this.tools = config.tools || [];
    }

    async complete(prompt) {
        const isMock = !this.apiKey || this.apiKey === 'mock_key' || this.apiKey.startsWith('mock');

        if (!isMock) {
            // 1. Real OpenRouter call
            try {
                const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.apiKey}`
                    },
                    body: JSON.stringify({
                        model: this.model,
                        messages: [{ role: 'user', content: prompt }]
                    })
                });
                
                if (res.ok) {
                    const data = await res.json();
                    if (data.text) {
                        return { text: data.text };
                    }
                    const text = data.choices?.[0]?.message?.content || '';
                    return { text };
                } else {
                    const errorText = await res.text().catch(() => '');
                    console.warn(`[OpenRouter API Error] Status: ${res.status}. Error: ${errorText}. Falling back to local Ollama.`);
                }
            } catch (e) {
                console.error('[OpenRouter Fetch Error] falling back to local Ollama:', e.message);
            }
        } else {
            // 2. Mock call (only for tests)
            try {
                const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt })
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.text) {
                        return { text: data.text };
                    }
                    const text = data.choices?.[0]?.message?.content || '';
                    return { text };
                }
            } catch (e) {
                console.error('[Mock/Test Fallback Fetch Error]:', e.message);
            }
        }

        // 3. Fallback to Ollama local
        try {
            const res = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: process.env.OLLAMA_DEFAULT_MODEL || 'qwen2.5-coder:7b',
                    prompt: prompt,
                    stream: false,
                    format: 'json'
                })
            });
            if (res.ok) {
                const data = await res.json();
                return { text: data.response || '' };
            } else {
                console.error(`[Ollama Local Error] Status: ${res.status}`);
            }
        } catch (e) {
            console.error('[Ollama Fallback Error]:', e.message);
        }

        return { text: '{}' };
    }
}

async function callCloudVision(imageBase64) {
  const apiKey = process.env.GOOGLE_MAPS_API_KEY;
  if (!apiKey) return { error: 'API Key not configured' };

  try {
    const res = await fetch(`https://vision.googleapis.com/v1/images:annotate?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requests: [{
          image: { content: imageBase64 },
          features: [
            { type: 'LABEL_DETECTION', maxResults: 15 },
            { type: 'LANDMARK_DETECTION', maxResults: 5 },
            { type: 'TEXT_DETECTION', maxResults: 5 }
          ]
        }]
      })
    });

    if (!res.ok) return { error: `Vision API error: ${res.status}` };
    const data = await res.json();
    const r = data.responses?.[0];
    if (!r || r.error) return { error: r?.error?.message || 'Empty response' };

    return {
      labels: (r.labelAnnotations || []).map(a => a.description),
      landmarks: (r.landmarkAnnotations || []).map(a => a.description),
      texts: (r.textAnnotations || []).map(a => a.description)
    };
  } catch (e) {
    return { error: e.message };
  }
}

// Zod Schema for Guardrails: Final Puzzle Response
const PuzzleResponseSchema = z.object({
    status: z.string(),
    clusterName: z.string(),
    confidence_score: z.number().min(0).max(1),
    requiresManualValidation: z.boolean(),
    anchorCount: z.number(),
    results: z.array(z.object({
        photoId: z.string(),
        evidence: z.string(),
        isAnchor: z.boolean(),
        name: z.string(),
        lat: z.number().nullable(),
        lng: z.number().nullable(),
        source: z.string()
    }))
});

function roundCoord(val) {
    if (val === null || val === undefined) return null;
    return Math.round(val * 10000) / 10000;
}

function generateClusterHash(photos) {
    const sorted = [...photos].sort((a, b) => a.id.localeCompare(b.id));
    const batchString = sorted.map(p => `${p.id}|${p.timestamp}|${p.lat}|${p.lng}`).join(';');
    return crypto.createHash('sha256').update(batchString).digest('hex');
}

// --- Agentic Tools Definition ---
const tools = {
    rankAnchors: tool({
        name: 'rankAnchors',
        description: 'Ranks photos to identify the best Anchor based on Landmarks, OCR, and GPS.',
        parameters: z.object({ photos: z.array(z.any()) }),
        execute: async ({ photos }) => {
            const scored = photos.map(p => {
                let score = 0;
                let pType = 'NONE';
                const labels = Array.isArray(p.visionLabels) ? p.visionLabels : [];
                const ocr = typeof p.ocrText === 'string' ? p.ocrText.trim() : '';

                const landmark = labels.find(l => l.isLandmark);
                if (landmark) { score = 1.0; pType = 'LANDMARK'; }
                else if (ocr.length > 3 && ocr.length < 60) { score = 0.8; pType = 'OCR_SHORT'; }
                else if (ocr.length >= 60) { score = 0.4; pType = 'OCR_LONG'; }
                else if (p.lat && p.lng) { score = 0.2; pType = 'GPS_ONLY'; }

                return { ...p, score, type: pType };
            });

            const sorted = scored.filter(p => p.score > 0).sort((a, b) => b.score - a.score || (a.gpsAccuracy || 999) - (b.gpsAccuracy || 999));
            return { bestAnchor: sorted[0], allScored: sorted };
        }
    }),

    cleanupOCR: tool({
        name: 'cleanupOCR',
        description: 'Uses local LLM to clean messy OCR text, correcting spelling errors and extracting official-looking business names.',
        parameters: z.object({ text: z.string() }),
        execute: async ({ text }) => {
            const ollamaModel = process.env.OLLAMA_DEFAULT_MODEL || 'qwen2.5-coder:7b';
            try {
                const prompt = `Limpia este texto OCR extraído de una imagen de local comercial para obtener el nombre oficial del establecimiento. Corrige errores ortográficos obvios y remueve caracteres basura.
TEXTO OCR: "${text}"
Retorna únicamente un JSON con la estructura: { "name": "Nombre Limpio" }`;
                const res = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: ollamaModel,
                        prompt: prompt,
                        stream: false,
                        format: 'json'
                    })
                });
                if (res.ok) {
                    const data = await res.json();
                    const cleaned = cleanJSONResponse(data.response);
                    try {
                        return JSON.parse(cleaned);
                    } catch {
                        return { name: text, raw_response: data.response };
                    }
                }
            } catch (e) {
                console.warn('[CleanupOCR Fail]:', e.message);
            }
            return { name: text, error: 'Ollama local not available' };
        }
    }),

    fuzzyReconcileOCR: tool({
        name: 'fuzzyReconcileOCR',
        description: 'Uses RapidFuzz (Token Set Ratio) in Python to compare OCR text with an official place name. Returns a similarity score and match status.',
        parameters: z.object({ ocrText: z.string(), officialName: z.string() }),
        execute: async ({ ocrText, officialName }) => {
            try {
                const result = await reconcileName(ocrText, officialName);
                return result;
            } catch (e) {
                console.error('[Fuzzy Reconcile Tool Fail]:', e.message);
                const score = calculateFallbackFuzzRatio(ocrText, officialName);
                return { score, match: score >= 75 };
            }
        }
    }),

    analyzeFisonomia: tool({
        name: 'analyzeFisonomia',
        description: 'Performs micro-architectural analysis using Google Cloud Vision + local LLM. Identifies furniture, wall coatings, and probable category.',
        parameters: z.object({ imageBase64: z.string() }),
        execute: async ({ imageBase64 }) => {
            const vision = await callCloudVision(imageBase64);
            if (vision.error) return { error: `Cloud Vision: ${vision.error}` };

            const prompt = `${MASTER_PROMPTS.FISONOMIA}

CLOUD VISION DATA:
Labels: ${(vision.labels || []).join(', ')}
Landmarks: ${(vision.landmarks || []).join(', ')}
Texts: ${(vision.texts || []).join(', ')}

Based on this data, infer the architectural details and return JSON.`;

            const ollamaModel = process.env.OLLAMA_DEFAULT_MODEL || 'qwen2.5-coder:7b';
            try {
                const res = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: ollamaModel,
                        prompt: prompt,
                        stream: false,
                        format: 'json'
                    })
                });
                if (res.ok) {
                    const data = await res.json();
                    const cleaned = cleanJSONResponse(data.response);
                    try {
                        return JSON.parse(cleaned);
                    } catch {
                        return { raw_response: data.response, error: 'Invalid JSON' };
                    }
                }
            } catch (e) {
                console.warn('[Fisonomia] Error:', e.message);
            }
            return { error: 'Vision analysis failed' };
        }
    }),

    analyzeSolarSync: tool({
        name: 'analyzeSolarSync',
        description: 'Performs solar synchronization analysis using Google Cloud Vision + local LLM. Compares shadow direction with theoretical sun position.',
        parameters: z.object({ 
            imageBase64: z.string(), 
            exifTime: z.string(), 
            estimatedLat: z.number(), 
            estimatedLng: z.number() 
        }),
        execute: async ({ imageBase64, exifTime, estimatedLat, estimatedLng }) => {
            const vision = await callCloudVision(imageBase64);
            if (vision.error) return { error: `Cloud Vision: ${vision.error}` };

            const prompt = MASTER_PROMPTS.SOLAR_SYNC
                .replace('{{exifTime}}', exifTime)
                .replace('{{lat}}', estimatedLat.toString())
                .replace('{{lng}}', estimatedLng.toString()) + `

CLOUD VISION DATA:
Labels: ${(vision.labels || []).join(', ')}
Landmarks: ${(vision.landmarks || []).join(', ')}
Texts: ${(vision.texts || []).join(', ')}

Based on this data, infer solar alignment and return JSON.`;

            const ollamaModel = process.env.OLLAMA_DEFAULT_MODEL || 'qwen2.5-coder:7b';
            try {
                const res = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: ollamaModel,
                        prompt: prompt,
                        stream: false,
                        format: 'json'
                    })
                });
                if (res.ok) {
                    const data = await res.json();
                    const cleaned = cleanJSONResponse(data.response);
                    try {
                        return JSON.parse(cleaned);
                    } catch {
                        return { raw_response: data.response, error: 'Invalid JSON' };
                    }
                }
            } catch (e) {
                console.warn('[SolarSync] Error:', e.message);
            }
            return { error: 'Solar synchronization failed' };
        }
    }),

    resolvePoi: tool({
        name: 'resolvePoi',
        description: 'Queries the geocoding cascade (Cache -> Google -> OpenCage) to find the official POI.',
        parameters: z.object({ lat: z.number(), lng: z.number(), keywords: z.string().optional(), radius: z.number().optional() }),
        execute: async ({ lat, lng, keywords, radius }) => {
            const result = await performGeocodingCascade(lat, lng, radius || 500, keywords);
            return { poi: result.name, address: result.address, source: result.source, confidence: result.confidence, place_id: result.place_id };
        }
    })
};

// Internal helper for resolving POI inside the agent
async function performGeocodingCascade(lat, lng, radius, keywords) {
    const roundedLat = roundCoord(lat);
    const roundedLng = roundCoord(lng);
    const h3Index = latLngToCell(roundedLat, roundedLng, H3_RESOLUTION);

    try {
        const cached = await memoryStore.findMatch(h3Index);
        if (cached) return { name: cached.name, address: null, source: 'LOCAL_CACHE_H3', confidence: 1.0, place_id: cached.place_id };
    } catch (e) { console.warn('[Cascade] L1 Fail:', e.message); }

    const GOOGLE_KEY = process.env.GOOGLE_MAPS_API_KEY;
    if (GOOGLE_KEY) {
        try {
            const res = await fetch('https://places.googleapis.com/v1/places:searchNearby', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': GOOGLE_KEY,
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.types'
                },
                body: JSON.stringify({
                    locationRestriction: { circle: { center: { latitude: lat, longitude: lng }, radius: radius } },
                    maxResultCount: 1
                })
            });
            if (res.ok) {
                const data = await res.json();
                const place = data.places?.[0];
                if (place && place.displayName?.text) {
                    return { name: place.displayName.text, address: place.formattedAddress, source: 'GOOGLE_PLACES_NEW', confidence: 0.99, place_id: place.id };
                }
            }
        } catch (e) { console.error('[Cascade] L2 Fail:', e.message); }
    }

    const OPENCAGE_KEY = process.env.OPENCAGE_API_KEY || process.env.VITE_OPENCAGE_API_KEY;
    // Preferir la clave de backend OPENCAGE_API_KEY; VITE_OPENCAGE_API_KEY funciona como fallback local/dev.
    if (OPENCAGE_KEY) {
        try {
            const res = await fetch(`https://api.opencagedata.com/geocode/v1/json?q=${roundedLat},${roundedLng}&key=${OPENCAGE_KEY}&language=es&no_annotations=1&no_record=true`);
            if (res.ok) {
                const data = await res.json();
                if (data.results?.length > 0) {
                    const best = data.results[0];
                    return { name: best.formatted, address: best.formatted, source: 'OPENCAGE', confidence: (best.confidence || 0) / 10, place_id: null };
                }
            }
        } catch (e) { console.warn('[Cascade] L3 Fail:', e.message); }
    }

    return { name: `${roundedLat}, ${roundedLng}`, address: "Unknown", source: 'COORDINATES_ONLY', confidence: 0.1, place_id: null };
}

export default async function (req, res) {
    if (req.method && req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const { photos } = req.body;
    if (!photos || !Array.isArray(photos) || photos.length === 0) return res.status(400).json({ error: 'photos array is required' });

    // PASO 1 DETERMINÍSTICO: Anonimización inmediata y forzada a 4 decimales para privacidad HIPAA/GDPR (0 días de retención GPS original)
    const anonymizedPhotos = photos.map(p => {
        const rounded = { ...p };
        if (rounded.lat !== null && rounded.lat !== undefined) {
            rounded.lat = roundCoord(rounded.lat);
        }
        if (rounded.lng !== null && rounded.lng !== undefined) {
            rounded.lng = roundCoord(rounded.lng);
        }
        return rounded;
    });

    const clusterHash = generateClusterHash(anonymizedPhotos);
    try {
        const cachedResult = await memoryStore.findClusterResult(clusterHash);
        if (cachedResult) return res.json({ ...cachedResult, status: 'SUCCESS', cache_hit: true });
    } catch (e) { console.warn('[Puzzle] Cache lookup failed'); }

    const agent = new Agent({
        apiKey: process.env.OPENROUTER_API_KEY,
        model: 'google/gemini-flash-1.5',
        tools: tools
    });

    const skills = await listAvailableSkills();
    const skillContext = await Promise.all(skills.map(s => loadSkill(s)));

    try {
        const proposalPrompt = `
            You are the Reverse-Geocoding Actor. Your goal is to propose the most likely "Truth of the Place" for this batch.
            
            PHOTOS (Already fully anonymized to 4 decimals): ${JSON.stringify(anonymizedPhotos)}
            SKILLS: ${skillContext.join('\n\n')}
            
            PROCESS:
            1. Use 'rankAnchors' to find the best candidate.
            2. Clean OCR with 'cleanupOCR' if needed.
            3. Use 'fuzzyReconcileOCR' to check OCR spelling against official names if applicable.
            4. Resolve official POI with 'resolvePoi'.
            5. CRITICAL: If confidence is < 75% or there is ambiguity between nearby places, you MUST invoke 'analyzeFisonomia' and 'analyzeSolarSync' to provide architectural and solar evidence.
            6. Propagate the results to the rest of the batch using the 15-min/H3 rule.
            
            Return a JSON following the PuzzleResponseSchema.
        `;

        const proposalResult = await agent.complete(proposalPrompt);
        let finalResult = JSON.parse(cleanJSONResponse(proposalResult.text));

        const reviewerPrompt = `
            You are a ruthless Geographic Auditor. Analyze this proposed result:
            RESULT: ${JSON.stringify(finalResult)}
            PHOTOS: ${JSON.stringify(anonymizedPhotos)}
            
            TASK: Find at least three potential flaws, logical gaps, or inconsistencies between the shadows, the architecture and the OCR. Do not praise the result; focus only on the weaknesses.
            
            Return a JSON with: { "is_valid": boolean, "flaws": ["string"], "suggested_correction": "string or null" }
        `;

        const auditResult = await agent.complete(reviewerPrompt);
        const audit = JSON.parse(cleanJSONResponse(auditResult.text));

        if (!audit.is_valid) {
            console.log('[Puzzle] Reviewer found flaws. Refining result...');
            const refinementPrompt = `
                The previous proposal was audited and found flawed: ${JSON.stringify(audit.flaws)}.
                Correct the result based on this critique.
                Original Proposal: ${JSON.stringify(finalResult)}
                Return the corrected JSON.
            `;
            const refinedResult = await agent.complete(refinementPrompt);
            finalResult = JSON.parse(cleanJSONResponse(refinedResult.text));
        }

        const validated = PuzzleResponseSchema.parse(finalResult);

        // PASO 7 DETERMINÍSTICO: Regla matemática exacta de herencia de 15 minutos en la misma celda H3
        const anchorResult = validated.results.find(r => r.isAnchor);
        const anchorPhoto = anonymizedPhotos.find(p => p.id === anchorResult?.photoId) || anonymizedPhotos[0];
        
        if (anchorResult && anchorResult.lat && anchorResult.lng) {
            validated.results = validated.results.map(r => {
                if (!r.isAnchor) {
                    const currentPhoto = anonymizedPhotos.find(p => p.id === r.photoId);
                    if (currentPhoto) {
                        const timeDiff = Math.abs(currentPhoto.timestamp - anchorPhoto.timestamp);
                        const isInWindow = timeDiff <= INHERIT_WINDOW_MS;
                        
                        if (isInWindow) {
                            r.lat = anchorResult.lat;
                            r.lng = anchorResult.lng;
                            r.name = anchorResult.name;
                            r.evidence = 'TIME_PROXIMITY';
                            r.source = 'INHERITED';
                        } else {
                            r.isAnchor = false;
                            r.evidence = 'NONE';
                            r.source = 'UNRESOLVED';
                            r.lat = currentPhoto.lat || null;
                            r.lng = currentPhoto.lng || null;
                        }
                    }
                }
                return r;
            });
        }

        const anchor = (anonymizedPhotos.find(p => p.id === validated.results.find(r => r.isAnchor)?.photoId) || anonymizedPhotos[0]);
        
        let consensus_result = null;
        try {
            const timestamp_str = anchor.timestamp ? new Date(anchor.timestamp).toISOString() : '';
            const ocr_score = anchor.ocrText ? (calculateFallbackFuzzRatio(anchor.ocrText, validated.clusterName) / 100.0) : 0.0;
            const has_landmark = anchor.visionLabels?.some(l => l.isLandmark || (l.description && l.score > 0.8)) || false;
            const landmark_score = has_landmark ? 1.0 : 0.0;
            const observed_shadow_direction = anchor.shadowDirection || anchor.direction || "North-East";

            consensus_result = await calculateConsensus({
                lat: anchor.lat,
                lng: anchor.lng,
                timestamp: timestamp_str,
                ocr_score: ocr_score,
                landmark_score: landmark_score,
                observed_shadow_direction: observed_shadow_direction
            });

            console.log('[Puzzle] Python Consensus Result:', consensus_result);

            if (consensus_result) {
                validated.confidence_score = consensus_result.confidence_score;
                validated.requiresManualValidation = (consensus_result.review_status === 'PENDING_REVIEW');
                validated.status = consensus_result.review_status; // 'RECONSTRUCTED', 'PENDING_REVIEW', 'REJECTED'
            }
        } catch (err) {
            console.error('[Puzzle] Error calling Python consensus microservice, falling back:', err.message);
        }

        if (validated.clusterName) {
            const reviewStatus = consensus_result ? consensus_result.review_status : 'RECONSTRUCTED';
            const evidence = consensus_result ? consensus_result.evidence : 'AGENTIC_CONSENSUS';
            await memoryStore.savePlace(
                validated.results.find(r => r.isAnchor)?.place_id || `unknown_${Date.now()}`,
                validated.clusterName,
                'point_of_interest',
                anchor.lat || 0,
                anchor.lng || 0,
                { method: 'AGENTIC_CONSENSUS', score: validated.confidence_score },
                validated.confidence_score,
                { evidence: evidence, solar_divergence: consensus_result?.solar_divergence },
                reviewStatus
            );
        }
        
        await memoryStore.saveClusterResult(clusterHash, validated);
        return res.json(validated);

    } catch (e) {
        console.error('[Puzzle Agent] Critical Error:', e);
        return res.status(500).json({ error: 'Agentic loop failed', details: e.message });
    }
}
