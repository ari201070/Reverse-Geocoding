import fetch from 'node-fetch';
import assert from 'node:assert/strict';

async function testClusterCache() {
    console.log("--- Testing Cluster Results Cache ---");
    
    const batch = {
        photos: [
            { id: 'p1', lat: -34.6037, lng: -58.3816, timestamp: 1700000000000, ocrText: 'Obelisco', visionLabels: [] },
            { id: 'p2', lat: null, lng: null, timestamp: 1700000001000, ocrText: '', visionLabels: [] }
        ]
    };

    try {
        console.log("Request 1 (Computing...)");
        const res1 = await fetch("http://localhost:3000/api/resolve-puzzle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(batch)
        });
        const data1 = await res1.json();
        console.log(`Result 1: ${data1.clusterName}, Cache Hit: ${data1.cache_hit || false}`);

        console.log("\nRequest 2 (Should hit cache...)");
        const res2 = await fetch("http://localhost:3000/api/resolve-puzzle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(batch)
        });
        const data2 = await res2.json();
        console.log(`Result 2: ${data2.clusterName}, Cache Hit: ${data2.cache_hit || false}`);

        if (data2.cache_hit) {
            console.log("\n✅ SUCCESS: Cluster cache working correctly!");
        } else {
            console.log("\n❌ FAILURE: Cache hit expected but not received.");
            process.exit(1);
        }
    } catch (e) {
        console.error("Test failed:", e.message);
        process.exit(1);
    }
}

testClusterCache();
