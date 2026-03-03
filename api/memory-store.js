const fs = require('fs');
const path = require('path');

// Local database path (JSON for simplicity as requested/Leaned)
const DATA_DIR = path.join(process.cwd(), '.data');
const MEMORY_FILE = path.join(DATA_DIR, 'spatial_memory.json');

/**
 * Spatial Memory Store: Manages the "Truth of the Place" discovered in batches.
 * This allows individual photo uploads to inherit context from previous searches.
 */
class MemoryStore {
    constructor() {
        this.ensureDir();
        this.memory = this.load();
    }

    ensureDir() {
        if (!fs.existsSync(DATA_DIR)) {
            fs.mkdirSync(DATA_DIR, { recursive: true });
        }
        if (!fs.existsSync(MEMORY_FILE)) {
            fs.writeFileSync(MEMORY_FILE, JSON.stringify({ clusters: [] }, null, 2));
        }
    }

    load() {
        try {
            const data = fs.readFileSync(MEMORY_FILE, 'utf8');
            return JSON.parse(data);
        } catch (e) {
            console.error('Error loading memory:', e);
            return { clusters: [] };
        }
    }

    save() {
        try {
            fs.writeFileSync(MEMORY_FILE, JSON.stringify(this.memory, null, 2));
        } catch (e) {
            console.error('Error saving memory:', e);
        }
    }

    /**
     * Find a matching location based on coordinates and time.
     * @param {number} lat 
     * @param {number} lng 
     * @param {number} timestamp 
     * @returns {Object|null}
     */
    findMatch(lat, lng, timestamp) {
        const LAT_THRESHOLD = 0.001; // ~100m
        const TIME_THRESHOLD = 2 * 60 * 60 * 1000; // 2 hours

        return this.memory.clusters.find(c => {
            const dist = Math.sqrt(Math.pow(c.lat - lat, 2) + Math.pow(c.lng - lng, 2));
            const timeDiff = Math.abs(c.timestamp - timestamp);
            return dist < LAT_THRESHOLD && timeDiff < TIME_THRESHOLD;
        });
    }

    /**
     * Store or update a location cluster.
     */
    addCluster(data) {
        const { lat, lng, timestamp, name, landmark, address } = data;
        
        // Update existing if very close, otherwise push new
        const existing = this.findMatch(lat, lng, timestamp);
        if (existing) {
            existing.name = name || existing.name;
            existing.landmark = landmark || existing.landmark;
            existing.address = address || existing.address;
            existing.timestamp = Math.max(existing.timestamp, timestamp);
        } else {
            this.memory.clusters.push({ lat, lng, timestamp, name, landmark, address });
        }
        this.save();
    }
}

module.exports = new MemoryStore();
