// api/resolve-puzzle.js - Agentic Batch Consensus Orchestrator (v5.0 - Industrial Grade)
import memoryStore from './memory-store.js';
import findPoiHandler from './find-poi.js';
import { sanitizeString as sanitize } from './python-service.js';
import { latLngToCell } from 'h3-js';
import crypto from 'crypto';
import { callModel, tool, createInitialState, buildTurnContext } from '@openrouter/agent';
import { z } from 'zod';
import { loadSkill, listAvailableSkills } from './utils/skill-loader.js';
import { MASTER_PROMPTS, cleanJSONResponse } from './utils/prompts.js';

// --- Configuration & Schemas ---
const H3_RESOLUTION = 9;
const INHERIT_WINDOW_MS = 15 * 60 * 1000;

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
        description: 'Uses local LLM (phi3) to extract the official place name from messy OCR text.',
        parameters: z.object({ text: z.string() }),
        execute: async ({ text }) => {
            try {
                const res = await fetch('http://localhost:11434/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: 'phi3',
                        prompt: MASTER_PROMPTS.FISONOMIA,
                        stream: false
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

    analyzeFisonomia: tool({
        name: 'analyzeFisonomia',
        description: 'Performs micro-architectural analysis using local Vision LLM (moondream). Identifies furniture, wall coatings, and probable category.',
        parameters: z.object({ imageBase64: z.string() }),
        execute: async ({ imageBase64 }) => {
            try {
                const res = await fetch('http://localhost:11434/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: 'moondream',
                        prompt: MASTER_PROMPTS.FISONOMIA,
                        images: [imageBase64],
                        stream: false
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
        description: 'Performs solar synchronization analysis using local Vision LLM. Compares shadow direction with theoretical sun position.',
        parameters: z.object({ 
            imageBase64: z.string(), 
            exifTime: z.string(), 
            estimatedLat: z.number(), 
            estimatedLng: z.number() 
        }),
        execute: async ({ imageBase64, exifTime, estimatedLat, estimatedLng }) => {
            try {
                const prompt = MASTER_PROMPTS.SOLAR_SYNC
                    .replace('{{exifTime}}', exifTime)
                    .replace('{{lat}}', estimatedLat.toString())
                    .replace('{{lng}', estimatedLng.toString());

                const res = await fetch('http://localhost:11434/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: 'moondream',
                        prompt: prompt,
                        images: [imageBase64],
                        stream: false
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
            return { poi: result.name, address: result.address, source: result.source, confidence: result.confidence };
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

    const clusterHash = generateClusterHash(photos);
    try {
        const cachedResult = await memoryStore.findClusterResult(clusterHash);
        if (cachedResult) return res.json({ ...cachedResult, status: 'SUCCESS', cache_hit: true });
    } catch (e) { console.warn('[Puzzle] Cache lookup failed'); }

    const agent = new Agent({
        apiKey: process.env.OPENROUTER_API_KEY,
        model: 'google/gemini-pro-1.5-flash',
        tools: tools
    });

    const skills = await listAvailableSkills();
    const skillContext = await Promise.all(skills.map(s => loadSkill(s)));

    try {
        const proposalPrompt = `
            You are the Reverse-Geocoding Actor. Your goal is to propose the most likely "Truth of the Place" for this batch.
            
            PHOTOS: ${JSON.stringify(photos)}
            SKILLS: ${skillContext.join('\n\n')}
            
            PROCESS:
            1. Use 'rankAnchors' to find the best candidate.
            2. Clean OCR with 'cleanupOCR' if needed.
            3. Resolve official POI with 'resolvePoi'.
            4. CRITICAL: If confidence is < 75% or there is ambiguity between nearby places, you MUST invoke 'analyzeFisonomia' and 'analyzeSolarSync' to provide architectural and solar evidence.
            5. Propagate the results to the rest of the batch using the 15-min/H3 rule.
            
            Return a JSON following the PuzzleResponseSchema.
        `;

        const proposalResult = await agent.complete(proposalPrompt);
        let finalResult = JSON.parse(cleanJSONResponse(proposalResult.text));

        const reviewerPrompt = `
            You are a ruthless Geographic Auditor. Analyze this proposed result:
            RESULT: ${JSON.stringify(finalResult)}
            PHOTOS: ${JSON.stringify(photos)}
            
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

        const anchor = (photos.find(p => p.id === validated.results.find(r => r.isAnchor)?.photoId) || photos[0]);
        if (validated.clusterName) {
            await memoryStore.savePlace(
                validated.results.find(r => r.isAnchor)?.place_id || 'unknown',
                validated.clusterName,
                'point_of_interest',
                anchor.lat || 0,
                anchor.lng || 0,
                { method: 'AGENTIC_CONSENSUS', score: validated.confidence_score }
            );
        }
        
        await memoryStore.saveClusterResult(clusterHash, validated);
        return res.json(validated);

    } catch (e) {
        console.error('[Puzzle Agent] Critical Error:', e);
        return res.status(500).json({ error: 'Agentic loop failed', details: e.message });
    }
}
