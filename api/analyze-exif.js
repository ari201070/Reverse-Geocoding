// api/analyze-exif.js - Bridge to Python EXIF Microservice
import { analyzeExif } from './python-service.js';
import Busboy from 'busboy';
import { Readable } from 'stream';

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    return new Promise((resolve) => {
        const busboy = Busboy({ headers: req.headers });
        let imageBuffer = null;

        busboy.on('file', (name, file, info) => {
            if (name === 'image') {
                const chunks = [];
                file.on('data', (data) => chunks.push(data));
                file.on('end', () => {
                    imageBuffer = Buffer.concat(chunks);
                });
            } else {
                file.resume();
            }
        });

        busboy.on('finish', async () => {
            try {
                if (!imageBuffer) {
                    throw new Error('No image field found in multipart request');
                }

                // Forward to Python microservice via python-service.js
                const result = await analyzeExif(imageBuffer);
                res.status(200).json(result);
                resolve();
            } catch (error) {
                console.error('[API] Error in analyze-exif bridge:', error.message);
                res.status(500).json({ error: error.message });
                resolve();
            }
        });

        busboy.on('error', (err) => {
            console.error('[API] Busboy error:', err);
            res.status(500).json({ error: 'Multipart parsing error' });
            resolve();
        });

        // pipe the rawBody buffer to busboy
        const stream = Readable.from(req.rawBody);
        stream.pipe(busboy);
    });
}
