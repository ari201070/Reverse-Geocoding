// lib/mcp-webfetch.js
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * Conector MCP para peticiones HTTP seguras.
 */
export async function mcpWebFetch(url) {
    console.log(`[MCP WebFetch] Consultando: ${url}`);
    try {
        // Usamos curl para una llamada robusta y portable en Windows/Linux
        const { stdout } = await execAsync(`curl -s -L "${url}"`);
        return stdout;
    } catch (err) {
        console.error(`[MCP WebFetch] Error en consulta: ${err.message}`);
        throw err;
    }
}
