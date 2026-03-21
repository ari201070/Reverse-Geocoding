const { Pool } = require('pg');
const h3 = require('h3-js');

const pool = new Pool({
    // Configuración de base de datos desde variables de entorno
});

/**
 * Gestor de Persistencia de la Lógica de Cascada (Nivel 1 - Caché Local).
 * Utiliza match exacto en índice H3 para resolver la identidad del lugar con costo $0.
 */
class MemoryStore {
    /**
     * Búsqueda de Alta Velocidad consultando known_places mediante H3.
     */
    async findMatch(lat, lng) {
        try {
            // Conversión antes de la base de datos (resolución 9)
            // Aseguramos el redondeo en memoria también (4 decimales para mayor consistencia de cluster)
            const roundedLat = Math.round(lat * 10000) / 10000;
            const roundedLng = Math.round(lng * 10000) / 10000;
            const hexId = h3.latLngToCell(roundedLat, roundedLng, 9);
            
            const query = `
                SELECT google_place_id, display_name 
                FROM known_places 
                WHERE h3_index_res9 = $1
                LIMIT 1
            `;
            
            // Match exacto operando sobre índice B-Tree (10 veces más rápido que ST_Distance)
            const { rows } = await pool.query(query, [hexId]);
            
            if (rows.length > 0) {
                // Resolución de Costo $0
                return rows[0]; 
            }
            return null;
        } catch (error) {
            console.error('Error al consultar Caché de Nivel 1:', error);
            return null;
        }
    }
}

module.exports = new MemoryStore();
