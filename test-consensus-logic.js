// test-consensus-logic.js
// Verification of 15-minute window and sanitization

const sanitize = (val) => typeof val === 'string' ? val.replace(/'/g, "''") : val;

function checkInheritance(anchorTs, photoTs) {
    const window = 15 * 60 * 1000;
    const diff = Math.abs(anchorTs - photoTs);
    return diff < window;
}

const mockAnchor = { timestamp: 1000000, name: "Earl's Court" };
const mockPhoto1 = { timestamp: 1000000 + 14 * 60 * 1000 }; // 14 min (Valid)
const mockPhoto2 = { timestamp: 1000000 + 16 * 60 * 1000 }; // 16 min (Invalid)

console.log("--- Testing Master Rules ---");
console.log(`Anchor: ${mockAnchor.name} at ${mockAnchor.timestamp}`);

const p1Valid = checkInheritance(mockAnchor.timestamp, mockPhoto1.timestamp);
const p1Name = p1Valid ? sanitize(mockAnchor.name) : "None";
console.log(`Photo 1 (14 min offset): Inherit? ${p1Valid} | Name: ${p1Name}`);

const p2Valid = checkInheritance(mockAnchor.timestamp, mockPhoto2.timestamp);
const p2Name = p2Valid ? sanitize(mockAnchor.name) : "None";
console.log(`Photo 2 (16 min offset): Inherit? ${p2Valid} | Name: ${p2Name}`);

if (p1Valid && !p2Valid && p1Name === "Earl''s Court") {
    console.log("✅ VERIFICATION SUCCESS: 15-min window and sanitization working correctly.");
} else {
    console.log("❌ VERIFICATION FAILED: Logic error found.");
}
