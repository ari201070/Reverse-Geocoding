// api/resolve-puzzle.js - Batch Consensus Orchestrator (Modo Puzzle)
// Identifies "Anchor Photos" and propagates context across a cluster.

const memoryStore = require('./memory-store');
const findPoiHandler = require('./find-poi');

/**
 * POST /api/resolve-puzzle
 * Body: { photos: [{ id, lat, lng, timestamp, visionLabels: [{name, isLandmark}], ocrText }] }
 */
module.exports = async (req, res) => {
    if (req.method && req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    /**
     * Sanitiza nombres según la regla de NotebookLM.
     */
    const sanitize = (val) => typeof val === 'string' ? val.replace(/'/g, "''") : val;

    const { photos } = req.body;
    if (!photos || !Array.isArray(photos) || photos.length === 0) {
        return res.status(400).json({ error: 'photos array is required' });
    }

    // 1. Identify "Anchor Photos" — those with Landmarks or high-confidence OCR
    const anchorPhotos = photos.filter(p =>
        p.visionLabels?.some(l => l.isLandmark) || (p.ocrText && p.ocrText.trim().length > 3)
    );

    // 2. Determine master context from the best anchor
    let masterContext = null;
    let masterLat = null, masterLng = null, masterTimestamp = null;

    if (anchorPhotos.length > 0) {
        const anchor = anchorPhotos[0];
        masterContext = anchor.visionLabels?.find(l => l.isLandmark)?.name || anchor.ocrText || null;
        masterLat = anchor.lat;
        masterLng = anchor.lng;
        masterTimestamp = anchor.timestamp;
    } else {
        // Fallback: use the first photo with GPS as anchor
        const gpsAnchor = photos.find(p => p.lat && p.lng);
        if (gpsAnchor) {
            masterLat = gpsAnchor.lat;
            masterLng = gpsAnchor.lng;
            masterTimestamp = gpsAnchor.timestamp;
        }
    }
    
    masterContext = sanitize(masterContext);

    // 3. Check spatial memory for the master location
    let memoryResult = null;
    if (masterLat && masterLng) {
        memoryResult = memoryStore.findMatch(masterLat, masterLng, Date.now());
        if (memoryResult && !masterContext) {
            masterContext = memoryResult.name;
        }
    }

    // 4. Process each photo — call find-poi for those with GPS, propagate to others
    const processedPhotos = await Promise.all(photos.map(async (photo) => {
        const isAnchor = anchorPhotos.includes(photo);

        // Photos with GPS: do an actual POI lookup
        if (photo.lat && photo.lng) {
            // Use internal call pattern instead of HTTP to find-poi
            let poiResult = null;
            const mockReq = {
                method: 'POST',
                body: {
                    lat: photo.lat,
                    lng: photo.lng,
                    timestamp: photo.timestamp || Date.now(),
                    keywords: masterContext || '',
                    landmarkFromVision: isAnchor
                        ? (photo.visionLabels?.find(l => l.isLandmark)?.name || photo.ocrText)
                        : masterContext,
                    radius: 300
                }
            };
            const mockRes = {
                status: () => mockRes,
                json: (data) => { poiResult = data; }
            };
            await findPoiHandler(mockReq, mockRes);

            return {
                photoId: photo.id,
                evidence: isAnchor ? 'ANCHOR_PHOTO' : 'GPS',
                isAnchor,
                name: poiResult?.data?.name || masterContext || null,
                address: poiResult?.data?.address || null,
                lat: photo.lat,
                lng: photo.lng,
                source: poiResult?.source || 'UNKNOWN'
            };
        } else {
            // Photos without GPS: inherit master context (Time Proximity rule: 15 min)
            const timeDiff = masterTimestamp ? Math.abs(photo.timestamp - masterTimestamp) : Infinity;
            const validInheritance = timeDiff < (15 * 60 * 1000);

            return {
                photoId: photo.id,
                evidence: validInheritance ? 'TIME_PROXIMITY' : 'NONE',
                isAnchor: false,
                name: validInheritance ? sanitize(masterContext) : null,
                address: null,
                lat: validInheritance ? masterLat : null,
                lng: validInheritance ? masterLng : null,
                source: validInheritance ? 'INHERITED_FROM_CLUSTER' : 'UNKNOWN',
                inherited: validInheritance
            };
        }
    }));

    return res.json({
        status: 'SUCCESS',
        batchId: `batch_${Date.now()}`,
        clusterName: masterContext || 'Cluster sin identificar',
        anchorCount: anchorPhotos.length,
        results: processedPhotos
    });
};
