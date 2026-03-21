// api/resolve-puzzle.js - Batch Consensus Orchestrator (Modo Puzzle)
// Identifies "Anchor Photos" and propagates context using Rules from NotebookLM (v3.2)
import memoryStore from './memory-store.js';
import findPoiHandler from './find-poi.js';
import { sanitizeString as sanitize } from './python-service.js';

/**
 * POST /api/resolve-puzzle
 * Body: { photos: [{ id, lat, lng, timestamp, visionLabels: [{name, isLandmark}], ocrText, gpsAccuracy }] }
 */
export default async function (req, res) {
    if (req.method && req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { photos } = req.body;
    if (!photos || !Array.isArray(photos) || photos.length === 0) {
        return res.status(400).json({ error: 'photos array is required' });
    }

    // --- Phase 1: Weighted Anchor Ranking (NotebookLM Rules) ---
    const scoredPhotos = photos.map(p => {
        let score = 0;
        let bestToken = null;
        let pType = 'NONE';

        // 1. Landmark (Master Clue) - 1.0
        const landmark = p.visionLabels?.find(l => l.isLandmark);
        if (landmark) {
            score = 1.0;
            bestToken = landmark.name;
            pType = 'LANDMARK';
        } 
        // 2. Short OCR (<60 characters) - 0.8
        else if (p.ocrText && p.ocrText.trim().length > 3 && p.ocrText.trim().length < 60) {
            score = 0.8;
            bestToken = p.ocrText.trim();
            pType = 'OCR_SHORT';
        }
        // 3. Long OCR / Ollama Required - 0.4
        else if (p.ocrText && p.ocrText.trim().length >= 60) {
            score = 0.4;
            bestToken = p.ocrText.trim();
            pType = 'OCR_LONG';
        }
        // 4. GPS Only - 0.2
        else if (p.lat && p.lng) {
            score = 0.2;
            pType = 'GPS_ONLY';
        }

        // Accuracy tie-breaker: convert to numeric (lower is better)
        const accuracy = parseFloat(p.gpsAccuracy) || 9999;

        return { ...p, score, bestToken, type: pType, accuracy };
    });

    // Pick the absolute best anchor
    // Rule: Lowest Accuracy is the secondary sort key for same score
    const sortedAnchors = scoredPhotos
        .filter(p => p.score > 0)
        .sort((a, b) => {
            if (b.score !== a.score) return b.score - a.score;
            return a.accuracy - b.accuracy; // Tie-break: lowest accuracy meters first
        });

    const masterAnchor = sortedAnchors[0];
    let masterContext = masterAnchor?.bestToken || null;
    let masterLat = masterAnchor?.lat || null;
    let masterLng = masterAnchor?.lng || null;
    let masterTimestamp = masterAnchor?.timestamp || null;

    // --- Phase 2: Intelligence - Ollama Context Cleanup ---
    // Rule: Use phi3 for OCR_LONG (Score 0.4)
    if (masterAnchor?.type === 'OCR_LONG' && masterContext) {
        try {
            const ollamaRes = await fetch('http://localhost:3000/api/ollama', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: 'phi3',
                    prompt: `Eres un experto en geolocalización. Dado el siguiente texto extraído de una foto por OCR, identifica el NOMBRE DEL LUGAR (ej: 'Teatro Colón', 'Rock & Feller\'s'). Si no puedes identificar un lugar específico, responde 'Desconocido'. Solo responde el nombre o 'Desconocido'. No agregues explicaciones.\n\nTexto: "${masterContext}"`,
                    stream: false
                })
            });

            if (ollamaRes.ok) {
                const ollamaData = await ollamaRes.json();
                const cleaned = ollamaData?.response?.trim();
                if (cleaned && cleaned !== 'Desconocido') {
                    masterContext = cleaned;
                }
            }
        } catch (e) {
            console.warn('[Puzzle] Ollama cleanup failed:', e.message);
        }
    }

    masterContext = sanitize(masterContext);

    // --- Phase 3: Spatial Memory lookup ---
    if (masterLat && masterLng && !masterContext) {
        const memoryResult = await memoryStore.findMatch(masterLat, masterLng);
        if (memoryResult) masterContext = memoryResult.name;
    }

    // --- Phase 4: Cluster Processing & Propagation ---
    const INHERIT_WINDOW_MS = 15 * 60 * 1000; // 15 min rule from NotebookLM

    const results = await Promise.all(scoredPhotos.map(async (photo) => {
        const isAnchor = photo.id === masterAnchor?.id;
        const timeDiff = masterTimestamp ? Math.abs(photo.timestamp - masterTimestamp) : Infinity;
        const canInherit = timeDiff <= INHERIT_WINDOW_MS;

        let finalLat = photo.lat || (canInherit ? masterLat : null);
        let finalLng = photo.lng || (canInherit ? masterLng : null);
        let evidence = 'NONE';
        let name = null;

        if (isAnchor) evidence = 'ANCHOR_PHOTO';
        else if (photo.lat && photo.lng) evidence = 'GPS';
        else if (canInherit) evidence = 'TIME_PROXIMITY';

        // Perform POI search for any photo with coords (original or inherited)
        if (finalLat && finalLng) {
            let poiResult = null;
            const mockReq = {
                body: {
                    lat: finalLat,
                    lng: finalLng,
                    timestamp: photo.timestamp,
                    keywords: (isAnchor || canInherit) ? masterContext : '',
                    landmarkFromVision: isAnchor ? photo.bestToken : (canInherit ? masterContext : null),
                    radius: 300
                }
            };
            const mockRes = {
                status: () => mockRes,
                json: (data) => { poiResult = data; }
            };
            await findPoiHandler(mockReq, mockRes);
            name = poiResult?.data?.name || masterContext;
        } else {
            name = masterContext;
        }

        return {
            photoId: photo.id,
            evidence,
            isAnchor,
            name: sanitize(name),
            lat: finalLat,
            lng: finalLng,
            source: isAnchor ? 'MASTER_SEÑAL' : (canInherit ? 'INHERITED' : 'INDIVIDUAL')
        };
    }));

    // Calculate overall confidence score
    // Rule: Confidence > 75% to proceed automatically
    const anchorScore = masterAnchor?.score || 0.1;
    const consistencyBonus = results.filter(r => r.name && r.name === results[0]?.name).length / results.length;
    const finalConfidence = Math.min(0.99, (anchorScore * 0.7) + (consistencyBonus * 0.3));

    return res.json({
        status: 'SUCCESS',
        batchId: `batch_${Date.now()}`,
        clusterName: masterContext || 'Ubicación Desconocida',
        confidence_score: finalConfidence,
        requiresManualValidation: finalConfidence < 0.75, // Rule: Halt if < 75%
        anchorCount: 1, // Focus on THE anchor
        results
    });
}
