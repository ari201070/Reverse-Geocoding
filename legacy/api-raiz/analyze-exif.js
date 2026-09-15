// api/analyze-exif.js - Pure JS EXIF Parser with Python fallback
import { analyzeExif } from './python-service.js';
import Busboy from 'busboy';
import { Readable } from 'stream';
import exifr from 'exifr';

function roundCoord(val) {
    if (val === null || val === undefined) return null;
    return Math.round(Number(val) * 10000) / 10000;
}

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
            // Default safe empty result to ensure the frontend never receives 500
            let result = {
                lat: null,
                lng: null,
                timestamp: '',
                gps_accuracy: '',
                direction: null
            };

            try {
                if (!imageBuffer || imageBuffer.length === 0) {
                    console.warn('[API] Empty or missing image field in multipart request');
                    res.status(200).json(result);
                    resolve();
                    return;
                }

                // 1. Try pure JS parsing first natively (extremely fast, robust, zero external dependencies)
                try {
                    const exifData = await exifr.parse(imageBuffer, {
                        gps: true,
                        exif: true,
                        xmp: true,
                        iptc: true
                    });

                    if (exifData) {
                        const lat = exifData.latitude || exifData.GPSLatitude || null;
                        const lng = exifData.longitude || exifData.GPSLongitude || null;
                        const timestampRaw = exifData.DateTimeOriginal || exifData.CreateDate || exifData.DateTime || '';
                        
                        let timestamp = '';
                        if (timestampRaw) {
                            if (timestampRaw instanceof Date) {
                                const pad = (num) => String(num).padStart(2, '0');
                                timestamp = `${timestampRaw.getFullYear()}:${pad(timestampRaw.getMonth() + 1)}:${pad(timestampRaw.getDate())} ${pad(timestampRaw.getHours())}:${pad(timestampRaw.getMinutes())}:${pad(timestampRaw.getSeconds())}`;
                            } else {
                                timestamp = String(timestampRaw);
                            }
                        }

                        const gps_accuracy = exifData.GPSHPositioningError !== undefined && exifData.GPSHPositioningError !== null
                            ? String(exifData.GPSHPositioningError)
                            : '';
                        
                        const direction = exifData.GPSImgDirection !== undefined && exifData.GPSImgDirection !== null
                            ? Math.round(Number(exifData.GPSImgDirection) * 100) / 100
                            : null;

                        result = {
                            lat: roundCoord(lat),
                            lng: roundCoord(lng),
                            timestamp,
                            gps_accuracy,
                            direction
                        };
                        console.log('[API] Extracted EXIF natively via exifr:', result);
                    }
                } catch (exifrError) {
                    console.warn('[API] Native exifr parsing failed:', exifrError.message);
                }

                // 2. If exifr couldn't get coordinates, only try Python service fallback if we have coordinates to look up, or as a last resort
                // But if the Python service is likely down or throws, we catch it silently and return our safe result.
                if (!result.lat || !result.lng) {
                    try {
                        // Check if Python service port is active or just call it with a fast timeout
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 1000); // 1s fast timeout
                        
                        const pyResult = await analyzeExif(imageBuffer, { signal: controller.signal });
                        clearTimeout(timeoutId);
                        
                        if (pyResult && (pyResult.lat || pyResult.lng)) {
                            result = {
                                lat: roundCoord(pyResult.lat),
                                lng: roundCoord(pyResult.lng),
                                timestamp: pyResult.timestamp || result.timestamp,
                                gps_accuracy: pyResult.gps_accuracy || result.gps_accuracy,
                                direction: pyResult.direction !== undefined ? pyResult.direction : result.direction
                            };
                            console.log('[API] Extracted EXIF via Python fallback:', result);
                        }
                    } catch (pythonError) {
                        // Silent catch - we already have a safe default result
                        console.log('[API] Python fallback skipped or failed (likely offline):', pythonError.message);
                    }
                }

                res.status(200).json(result);
                resolve();
            } catch (error) {
                console.error('[API] Critical Error in analyze-exif handler, returning safe default:', error.message);
                res.status(200).json(result);
                resolve();
            }
        });

        busboy.on('error', (err) => {
            console.error('[API] Busboy error:', err);
            res.status(200).json({
                lat: null,
                lng: null,
                timestamp: '',
                gps_accuracy: '',
                direction: null,
                error: 'Multipart parsing error'
            });
            resolve();
        });

        if (req.rawBody) {
            const stream = Readable.from(req.rawBody);
            stream.pipe(busboy);
        } else {
            req.pipe(busboy);
        }
    });
}
