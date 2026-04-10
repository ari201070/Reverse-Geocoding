import fetch from 'node-fetch';

async function testCascade() {
    console.log("--- Testing Geocoding Cascade ---");
    
    const obelisco = { lat: -34.6037, lng: -58.3816 };
    
    try {
        console.log("Request 1 (Initial Lookup):");
        const res1 = await fetch("http://localhost:3000/api/find-poi", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(obelisco)
        });
        const data1 = await res1.json();
        console.log(`Source: ${data1.data.source}, Name: ${data1.data.name}`);

        console.log("\nWaiting for persistence...");
        await new Promise(r => setTimeout(r, 1000));

        console.log("Request 2 (Should hit Level 1 Cache):");
        const res2 = await fetch("http://localhost:3000/api/find-poi", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(obelisco)
        });
        const data2 = await res2.json();
        console.log(`Source: ${data2.data.source}, Name: ${data2.data.name}`);
        
        if (data2.data.source === 'LOCAL_CACHE_H3') {
            console.log("\n✅ SUCCESS: Level 1 Cache hit confirmed!");
        } else {
            console.log("\n❌ FAILURE: Level 1 Cache hit expected but got " + data2.data.source);
        }

    } catch (e) {
        console.error("Test failed:", e.message);
    }
}

testCascade();
