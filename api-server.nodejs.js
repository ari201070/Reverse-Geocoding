/**
 * api-server.nodejs.js
 * Servidor mínimo para ejecutar las funciones de la carpeta /api localmente.
 * Simula el comportamiento de Vercel Serverless Functions.
 */

import http from 'http';
import url from 'url';
import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';
import 'dotenv/config';

const PORT = 3000;

console.log(`[INIT] Probando configuración...`);
console.log(`[INIT] GOOGLE_MAPS_API_KEY: ${process.env.GOOGLE_MAPS_API_KEY ? 'Cargada (OK)' : 'NO ENCONTRADA (Check .env)'}`);

const server = http.createServer(async (req, res) => {
    // CORS simplificado para desarrollo
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;

    // Solo manejamos rutas que empiecen con /api/
    if (pathname && pathname.startsWith('/api/')) {
        const endpoint = pathname.replace('/api/', '');
        const filePath = path.join(process.cwd(), 'api', `${endpoint}.js`);

        if (fs.existsSync(filePath)) {
            try {
                console.log(`[API] Invocando: ${endpoint} (${req.method})`);
                
                // Mock de Vercel Request/Response con path compatible para Windows
                const fileUrl = pathToFileURL(filePath).href;
                const module = await import(fileUrl);
                const handler = module.default || module; // Soporte CJS/ESM
                
                // Leer body solo si hay datos (POST/PUT)
                let chunks = [];
                await new Promise((resolve) => {
                    req.on('data', chunk => { chunks.push(chunk); });
                    req.on('end', resolve);
                });
                const rawBody = Buffer.concat(chunks);

                let parsedBody = {};
                const contentType = req.headers['content-type'] || '';
                if (contentType.includes('application/json') && rawBody.length > 0) {
                    try {
                        parsedBody = JSON.parse(rawBody.toString());
                    } catch (e) {
                        console.warn(`[API] No se pudo parsear el body como JSON`);
                    }
                }

                const vercelReq = {
                    ...req,
                    body: parsedBody,
                    rawBody: rawBody, // Preservar para multipart
                    query: parsedUrl.query,
                    method: req.method,
                    headers: req.headers
                };

                const vercelRes = {
                    status: (code) => {
                        res.statusCode = code;
                        return vercelRes;
                    },
                    json: (data) => {
                        if (!res.writableEnded) {
                            res.setHeader('Content-Type', 'application/json');
                            res.end(JSON.stringify(data));
                        }
                        return vercelRes;
                    },
                    send: (data) => {
                        if (!res.writableEnded) {
                            res.end(data);
                        }
                        return vercelRes;
                    },
                    setHeader: (name, value) => {
                        res.setHeader(name, value);
                        return vercelRes;
                    }
                };

                if (typeof handler === 'function') {
                    await handler(vercelReq, vercelRes);
                } else if (handler.default && typeof handler.default === 'function') {
                    await handler.default(vercelReq, vercelRes);
                } else {
                    throw new Error(`El archivo ${endpoint}.js no exporta una función válida`);
                }
            } catch (err) {
                console.error(`❌ Error en API ${endpoint}:`, err);
                if (!res.writableEnded) {
                    res.statusCode = 500;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: err.message, stack: err.stack }));
                }
            }
        } else {
            res.statusCode = 404;
            res.end(JSON.stringify({ error: `Not Found: ${filePath}` }));
        }
    } else {
        res.statusCode = 404;
        res.end('Not Found');
    }
});

server.listen(PORT, () => {
    console.log(`🚀 API Server (Vercel Simulation) running at http://localhost:${PORT}`);
    console.log(`   Mapping /api/* to local folder ./api/*.js`);
});
