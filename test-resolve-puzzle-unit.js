import resolvePuzzle from './api/resolve-puzzle.js';
import memoryStore from './api/memory-store.js';

// Mocking the environment
process.env.OPENROUTER_API_KEY = 'mock_key';
process.env.DATABASE_URL = 'postgresql://user:pass@localhost:5432/db';

// Simple Mock for memoryStore
// Since memoryStore is a default export instance, we can overwrite its methods
memoryStore.findClusterResult = async () => null;
memoryStore.saveClusterResult = async () => { console.log("[Mock] Saved cluster result"); return true; };
memoryStore.savePlace = async () => { console.log("[Mock] Saved place to Sovereign Memory"); return true; };

// Mocking fetch
global.fetch = async (url, options) => {
    console.log(`[Mock Fetch] Calling: ${url}`);
    if (url.includes('localhost:11434')) {
        return {
            ok: true,
            json: async () => ({ response: '{"mobiliario": "Sillas de madera", "categoria_probable": "Bodegon"}' })
        };
    }
    if (url.includes('openrouter.ai')) {
        return {
            ok: true,
            json: async () => ({ 
                text: JSON.stringify({
                    status: 'SUCCESS',
                    clusterName: 'El Boliche de Nico',
                    confidence_score: 0.95,
                    requiresManualValidation: false,
                    anchorCount: 1,
                    results: [
                        { photoId: 'p1', evidence: 'ANCHOR_PHOTO', isAnchor: true, name: 'El Boliche de Nico', lat: -34.6037, lng: -58.3816, source: 'MASTER' },
                        { photoId: 'p2', evidence: 'TIME_PROXIMITY', isAnchor: false, name: 'El Boliche de Nico', lat: -34.6037, lng: -58.3816, source: 'INHERITED' }
                    ]
                }) 
            })
        };
    }
    return { ok: false, status: 404 };
};

async function runTest() {
    console.log("--- Testing Resolve-Puzzle Agentic Loop ---");
    
    const req = {
        method: 'POST',
        body: {
            photos: [
                { id: 'p1', lat: -34.6037, lng: -58.3816, timestamp: 1700000000000, ocrText: 'Boliche de Nico', visionLabels: [] },
                { id: 'p2', lat: null, lng: null, timestamp: 1700000001000, ocrText: '', visionLabels: [] }
            ]
        }
    };

    const res = {
        status: (code) => { console.log(`Status: ${code}`); return res; },
        json: (data) => { 
            console.log("Final Response:", JSON.stringify(data, null, 2));
            return data;
        }
    };

    try {
        await resolvePuzzle(req, res);
        console.log("\n✅ SUCCESS: Agentic loop completed successfully!");
    } catch (e) {
        console.error("\n❌ FAILURE:", e);
    }
}

runTest();
