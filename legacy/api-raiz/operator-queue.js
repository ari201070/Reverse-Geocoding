// api/operator-queue.js - Human-in-the-Loop Review Queue API (Antigravity 2.0)
import memoryStore from './memory-store.js';

export default async function handler(req, res) {
    if (req.method === 'GET') {
        try {
            const pending = await memoryStore.getPendingReviews();
            return res.status(200).json(pending);
        } catch (error) {
            console.error('[API Queue] Error fetching pending reviews:', error.message);
            return res.status(500).json({ error: error.message });
        }
    } else if (req.method === 'POST') {
        try {
            const { id, action, correctedData } = req.body;
            if (!id || !action) {
                return res.status(400).json({ error: 'id and action are required' });
            }

            const success = await memoryStore.resolveReview(id, action, correctedData || {});
            if (success) {
                return res.status(200).json({ success: true, message: `Review ${id} resolved with action ${action}` });
            } else {
                return res.status(500).json({ success: false, error: 'Failed to update database record' });
            }
        } catch (error) {
            console.error('[API Queue] Error resolving review:', error.message);
            return res.status(500).json({ error: error.message });
        }
    } else {
        return res.status(405).json({ error: 'Method not allowed' });
    }
}
