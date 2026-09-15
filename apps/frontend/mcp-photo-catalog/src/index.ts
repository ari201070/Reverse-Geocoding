#!/usr/bin/env node

/**
 * Photo Catalog MCP Server
 * 
 * MCP Server para photo_catalog.db - 29,648 fotos con metadatos
 * Permite consultar y actualizar la base de datos de fotos del proyecto
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Ruta a la base de datos
function resolveDbPath(): string {
  const raw = process.env.PHOTO_CATALOG_DB;
  if (raw && raw.trim() !== "") {
    return raw.replace(/\\/g, "/");
  }
  return path.join(__dirname, "..", "..", "..", "..", "data", "photo_catalog.db");
}
const DB_PATH = resolveDbPath();

// Conexión a la base de datos
let db: Database.Database;

function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma("journal_mode = WAL");
  }
  return db;
}

// Definición de herramientas
const tools: Tool[] = [
  {
    name: "get_stats",
    description: "Obtiene estadísticas generales del catálogo de fotos (total, con GPS, duplicados, etc.)",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "search_photos",
    description: "Busca fotos por ubicación, fecha, fuente u otros criterios",
    inputSchema: {
      type: "object",
      properties: {
        country: { type: "string", description: "Filtrar por país" },
        city: { type: "string", description: "Filtrar por ciudad" },
        year: { type: "string", description: "Filtrar por año (ej: 2025)" },
        source: { type: "string", description: "Filtrar por fuente (unified_disk, etc.)" },
        has_gps: { type: "boolean", description: "Solo fotos con GPS" },
        limit: { type: "number", description: "Número máximo de resultados (default: 100)" },
      },
      required: [],
    },
  },
  {
    name: "get_photos_without_gps",
    description: "Obtiene fotos que necesitan geolocalización (sin latitude/longitude)",
    inputSchema: {
      type: "object",
      properties: {
        year: { type: "string", description: "Filtrar por año" },
        limit: { type: "number", description: "Número máximo de resultados (default: 50)" },
      },
      required: [],
    },
  },
  {
    name: "get_geocoding_stats",
    description: "Obtiene estadísticas de geolocalización por país y ciudad",
    inputSchema: {
      type: "object",
      properties: {
        country: { type: "string", description: "Filtrar por país específico" },
      },
      required: [],
    },
  },
  {
    name: "get_photo_info",
    description: "Obtiene información detallada de una foto por ID o nombre de archivo",
    inputSchema: {
      type: "object",
      properties: {
        photo_id: { type: "number", description: "ID de la foto" },
        filename: { type: "string", description: "Nombre del archivo" },
      },
      required: [],
    },
  },
  {
    name: "update_photo_metadata",
    description: "Actualiza los metadatos de una foto (ubicación, ciudad, país, etc.)",
    inputSchema: {
      type: "object",
      properties: {
        photo_id: { type: "number", description: "ID de la foto a actualizar" },
        location_name: { type: "string", description: "Nuevo nombre de ubicación" },
        location_address: { type: "string", description: "Nueva dirección" },
        country: { type: "string", description: "Nuevo país" },
        city: { type: "string", description: "Nueva ciudad" },
        latitude: { type: "number", description: "Nueva latitud" },
        longitude: { type: "number", description: "Nueva longitud" },
      },
      required: ["photo_id"],
    },
  },
  {
    name: "find_location_clusters",
    description: "Encuentra clusters de ubicaciones (agrupa coordenadas cercanas) para identificar lugares visitados",
    inputSchema: {
      type: "object",
      properties: {
        year: { type: "string", description: "Filtrar por año (ej: 2025)" },
        month: { type: "string", description: "Filtrar por mes (ej: 09)" },
        precision: { type: "number", description: "Precisión decimal para agrupar (default: 4 = ~11m)" },
        limit: { type: "number", description: "Número máximo de clusters (default: 20)" },
      },
      required: [],
    },
  },
  {
    name: "check_fallback_locations",
    description: "Identifica fotos con nombres de ubicación 'Fallback' o vacíos que necesitan geocodificación",
    inputSchema: {
      type: "object",
      properties: {
        year: { type: "string", description: "Filtrar por año (ej: 2025)" },
        month: { type: "string", description: "Filtrar por mes (ej: 09)" },
        limit: { type: "number", description: "Número máximo de resultados (default: 30)" },
      },
      required: [],
    },
  },
  {
    name: "get_geocoding_quality_report",
    description: "Genera reporte de calidad de geocodificación por país/ciudad",
    inputSchema: {
      type: "object",
      properties: {
        country: { type: "string", description: "Filtrar por país específico" },
      },
      required: [],
    },
  },
  {
    name: "find_duplicates",
    description: "Busca fotos duplicadas basándose en hash SHA256",
    inputSchema: {
      type: "object",
      properties: {
        include_original: { type: "boolean", description: "Incluir foto original en resultados (default: false)" },
        limit: { type: "number", description: "Número máximo de grupos duplicados (default: 50)" },
      },
      required: [],
    },
  },
  {
    name: "get_db_schema",
    description: "Obtiene el esquema completo de la base de datos",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "check_camera_distribution",
    description: "Analiza distribución de cámaras por año/mes (requiere acceso a archivos físicos)",
    inputSchema: {
      type: "object",
      properties: {
        year_range: { type: "string", description: "Rango de años (ej: 2002-2012)" },
      },
      required: [],
    },
  },
];

// Manejadores de herramientas
async function handleToolCall(name: string, args: any): Promise<any> {
  const database = getDb();

  switch (name) {
    case "get_stats": {
      const getCount = (query: string) => (database.prepare(query).get() as { count: number }).count;
      const stats = {
        total_photos: getCount("SELECT COUNT(*) as count FROM photos"),
        with_gps: getCount("SELECT COUNT(*) as count FROM photos WHERE latitude IS NOT NULL AND longitude IS NOT NULL"),
        without_gps: getCount("SELECT COUNT(*) as count FROM photos WHERE latitude IS NULL OR longitude IS NULL"),
        with_location_name: getCount("SELECT COUNT(*) as count FROM photos WHERE location_name IS NOT NULL"),
        with_country: getCount("SELECT COUNT(*) as count FROM photos WHERE country IS NOT NULL"),
        with_city: getCount("SELECT COUNT(*) as count FROM photos WHERE city IS NOT NULL"),
        duplicates: getCount("SELECT COUNT(*) as count FROM photos WHERE is_duplicate = 1"),
        by_source: database.prepare("SELECT folder_source, COUNT(*) as count FROM photos GROUP BY folder_source ORDER BY count DESC").all(),
        by_year: database.prepare(`
          SELECT 
            SUBSTR(date_taken, 1, 4) as year, 
            COUNT(*) as count 
          FROM photos 
          WHERE date_taken IS NOT NULL 
          GROUP BY year 
          ORDER BY year
        `).all(),
      };
      return { content: [{ type: "text", text: JSON.stringify(stats, null, 2) }] };
    }

    case "search_photos": {
      let query = "SELECT * FROM photos WHERE 1=1";
      const queryParams: any[] = [];

      if (args.country) {
        query += " AND country = ?";
        queryParams.push(args.country);
      }
      if (args.city) {
        query += " AND city = ?";
        queryParams.push(args.city);
      }
      if (args.year) {
        query += " AND date_taken LIKE ?";
        queryParams.push(`${args.year}%`);
      }
      if (args.source) {
        query += " AND folder_source = ?";
        queryParams.push(args.source);
      }
      if (args.has_gps) {
        query += " AND latitude IS NOT NULL AND longitude IS NOT NULL";
      }

      query += " ORDER BY date_taken DESC LIMIT ?";
      queryParams.push(args.limit || 100);

      const photos = database.prepare(query).all(...queryParams);
      return { content: [{ type: "text", text: JSON.stringify(photos, null, 2) }] };
    }

    case "get_photos_without_gps": {
      let query = "SELECT * FROM photos WHERE (latitude IS NULL OR longitude IS NULL)";
      const queryParams: any[] = [];

      if (args.year) {
        query += " AND date_taken LIKE ?";
        queryParams.push(`${args.year}%`);
      }

      query += " ORDER BY date_taken DESC LIMIT ?";
      queryParams.push(args.limit || 50);

      const photos = database.prepare(query).all(...queryParams);
      return { content: [{ type: "text", text: JSON.stringify(photos, null, 2) }] };
    }

    case "get_geocoding_stats": {
      let query = `
        SELECT 
          country,
          city,
          COUNT(*) as total_photos,
          SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as with_gps,
          SUM(CASE WHEN location_name IS NOT NULL THEN 1 ELSE 0 END) as with_location
        FROM photos 
        WHERE country IS NOT NULL
      `;
      const queryParams: any[] = [];

      if (args.country) {
        query += " AND country = ?";
        queryParams.push(args.country);
      }

      query += " GROUP BY country, city ORDER BY total_photos DESC";

      const stats = database.prepare(query).all(...queryParams);
      return { content: [{ type: "text", text: JSON.stringify(stats, null, 2) }] };
    }

    case "get_photo_info": {
      let photo;
      if (args.photo_id) {
        photo = database.prepare("SELECT * FROM photos WHERE id = ?").get(args.photo_id);
      } else if (args.filename) {
        photo = database.prepare("SELECT * FROM photos WHERE filename = ?").get(args.filename);
      }

      if (!photo) {
        return { content: [{ type: "text", text: "Foto no encontrada" }] };
      }

      return { content: [{ type: "text", text: JSON.stringify(photo, null, 2) }] };
    }

    case "update_photo_metadata": {
      const writeDb = new Database(DB_PATH, { readonly: false });
      writeDb.pragma("journal_mode = WAL");

      const updates: string[] = [];
      const values: any[] = [];

      if (args.location_name !== undefined) {
        updates.push("location_name = ?");
        values.push(args.location_name);
      }
      if (args.location_address !== undefined) {
        updates.push("location_address = ?");
        values.push(args.location_address);
      }
      if (args.country !== undefined) {
        updates.push("country = ?");
        values.push(args.country);
      }
      if (args.city !== undefined) {
        updates.push("city = ?");
        values.push(args.city);
      }
      if (args.latitude !== undefined) {
        updates.push("latitude = ?");
        values.push(args.latitude);
      }
      if (args.longitude !== undefined) {
        updates.push("longitude = ?");
        values.push(args.longitude);
      }

      if (updates.length === 0) {
        writeDb.close();
        return { content: [{ type: "text", text: "No se especificaron campos para actualizar" }] };
      }

      values.push(args.photo_id);
      const result = writeDb.prepare(`UPDATE photos SET ${updates.join(", ")} WHERE id = ?`).run(...values);
      writeDb.close();

      return { 
        content: [{ 
          type: "text", 
          text: `Foto ${args.photo_id} actualizada. Filas afectadas: ${result.changes}` 
        }] 
      };
    }

    case "find_location_clusters": {
      let query = `
        SELECT 
          round(latitude, ${args.precision || 4}) as lat_r,
          round(longitude, ${args.precision || 4}) as lng_r,
          location_name,
          city,
          country,
          COUNT(*) as photo_count,
          MIN(date_taken) as first_date,
          MAX(date_taken) as last_date
        FROM photos 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
      `;
      const queryParams: any[] = [];

      if (args.year) {
        query += " AND date_taken LIKE ?";
        queryParams.push(`${args.year}%`);
      }
      if (args.month) {
        query += " AND date_taken LIKE ?";
        queryParams.push(`${args.year || '%'}-${args.month}%`);
      }

      query += `
        GROUP BY lat_r, lng_r
        ORDER BY photo_count DESC
        LIMIT ${args.limit || 20}
      `;

      const clusters = database.prepare(query).all(...queryParams);
      return { content: [{ type: "text", text: JSON.stringify(clusters, null, 2) }] };
    }

    case "check_fallback_locations": {
      let query = `
        SELECT 
          round(latitude, 3) as lat_r,
          round(longitude, 3) as lng_r,
          location_name,
          COUNT(*) as count,
          MIN(date_taken) as first_date,
          MAX(date_taken) as last_date
        FROM photos 
        WHERE latitude IS NOT NULL 
          AND (location_name LIKE '%Fallback%' OR location_name IS NULL OR location_name = '')
      `;
      const queryParams: any[] = [];

      if (args.year) {
        query += " AND date_taken LIKE ?";
        queryParams.push(`${args.year}%`);
      }
      if (args.month) {
        query += " AND date_taken LIKE ?";
        queryParams.push(`${args.year || '%'}-${args.month}%`);
      }

      query += `
        GROUP BY lat_r, lng_r
        ORDER BY count DESC
        LIMIT ${args.limit || 30}
      `;

      const fallbacks = database.prepare(query).all(...queryParams);
      return { content: [{ type: "text", text: JSON.stringify(fallbacks, null, 2) }] };
    }

    case "get_geocoding_quality_report": {
      let query = `
        SELECT 
          country,
          city,
          COUNT(*) as total_photos,
          SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as with_gps,
          SUM(CASE WHEN location_name IS NOT NULL AND location_name NOT LIKE '%Fallback%' AND location_name != '' THEN 1 ELSE 0 END) as with_proper_location,
          SUM(CASE WHEN location_name LIKE '%Fallback%' OR location_name IS NULL OR location_name = '' THEN 1 ELSE 0 END) as fallback_or_empty,
          SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as gps_percentage
        FROM photos 
        WHERE country IS NOT NULL
      `;
      const queryParams: any[] = [];

      if (args.country) {
        query += " AND country = ?";
        queryParams.push(args.country);
      }

      query += " GROUP BY country, city ORDER BY total_photos DESC";

      const report = database.prepare(query).all(...queryParams);
      return { content: [{ type: "text", text: JSON.stringify(report, null, 2) }] };
    }

    case "find_duplicates": {
      interface DuplicateRow {
        sha256: string;
        count: number;
        paths: string;
        ids: string;
      }
      const duplicates = database.prepare(`
        SELECT 
          sha256,
          COUNT(*) as count,
          GROUP_CONCAT(file_path) as paths,
          GROUP_CONCAT(id) as ids
        FROM photos 
        WHERE sha256 IS NOT NULL
        GROUP BY sha256
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT ${args.limit || 50}
      `).all() as DuplicateRow[];

      const result = args.include_original ? duplicates : duplicates.map(d => ({
        sha256: d.sha256,
        count: d.count,
        duplicate_paths: d.paths.split(',').slice(1),
        duplicate_ids: d.ids.split(',').slice(1),
        original_path: d.paths.split(',')[0],
        original_id: d.ids.split(',')[0]
      }));

      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    case "get_db_schema": {
      const schema = database.prepare("PRAGMA table_info(photos)").all();
      const indexes = database.prepare("PRAGMA index_list(photos)").all();
      const foreignKeys = database.prepare("PRAGMA foreign_key_list(photos)").all();

      return { 
        content: [{ 
          type: "text", 
          text: JSON.stringify({
            columns: schema,
            indexes: indexes,
            foreign_keys: foreignKeys
          }, null, 2) 
        }] 
      };
    }

    case "check_camera_distribution": {
      return { 
        content: [{ 
          type: "text", 
          text: "Para análisis de cámaras se necesita acceso a archivos físicos en disco F. Ejecuta check_cameras_exif.py directamente." 
        }] 
      };
    }

    default:
      return { 
        content: [{ type: "text", text: `Herramienta desconocida: ${name}` }],
        isError: true,
      };
  }
}

// Crear servidor MCP
const server = new Server(
  {
    name: "photo-catalog",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Registrar handler para listar herramientas
server.setRequestHandler(ListToolsRequestSchema, async () => {
  console.error("📋 [MCP] list_tools request received");
  return { tools };
});

// Registrar handler para llamadas a herramientas
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  console.error(`🔧 [MCP] Tool call: ${name}`);

  try {
    const result = await handleToolCall(name, args || {});
    return result;
  } catch (error) {
    console.error(`❌ [MCP] Error: ${error}`);
    return {
      content: [{ type: "text", text: `Error: ${error}` }],
      isError: true,
    };
  }
});

// Iniciar servidor
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("🚀 MCP Photo Catalog Server iniciado");
  console.error(`📁 Base de datos: ${DB_PATH}`);
}

main().catch(console.error);