import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";
import exifr from "exifr";
import "dotenv/config";

// Import handlers from /api directory
import findPoiHandler from "../api/find-poi.js";
import analyzeImageHandler from "../api/analyze-image.js";
import resolvePuzzleHandler from "../api/resolve-puzzle.js";

// Initialize the MCP server
const server = new Server(
  {
    name: "reverse-geocoding-api",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define tools list
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "find_poi",
        description: "Encuentra puntos de interés (POIs) cercanos a coordenadas dadas utilizando una cascada de servicios (Caché local, Google Places, OpenCage).",
        inputSchema: {
          type: "object",
          properties: {
            lat: { type: "number", description: "Latitud del lugar (-90 a 90)" },
            lng: { type: "number", description: "Longitud del lugar (-180 a 180)" },
            radius: { type: "number", description: "Radio de búsqueda en metros (por defecto 500)" },
            keywords: { type: "string", description: "Palabras clave o contexto visual para refinar la búsqueda" }
          },
          required: ["lat", "lng"]
        }
      },
      {
        name: "analyze_exif",
        description: "Extrae metadatos EXIF (coordenadas GPS, timestamp, orientación de cámara, precisión) de una imagen local utilizando un parser de alto rendimiento.",
        inputSchema: {
          type: "object",
          properties: {
            filePath: { type: "string", description: "Ruta absoluta del archivo de imagen en el sistema" }
          },
          required: ["filePath"]
        }
      },
      {
        name: "analyze_image",
        description: "Analiza el contenido visual de una imagen local mediante Google Cloud Vision API para extraer etiquetas, hitos y texto OCR.",
        inputSchema: {
          type: "object",
          properties: {
            filePath: { type: "string", description: "Ruta absoluta del archivo de imagen en el sistema" }
          },
          required: ["filePath"]
        }
      },
      {
        name: "resolve_puzzle",
        description: "Ejecuta el orquestador de consenso para un lote de fotos, aplicando reglas espacio-temporales y consenso para encontrar la verdad de la ubicación.",
        inputSchema: {
          type: "object",
          properties: {
            photos: {
              type: "array",
              description: "Lista de objetos de fotos con metadatos EXIF y análisis visual",
              items: {
                type: "object",
                properties: {
                  id: { type: "string", description: "ID único o nombre del archivo de la foto" },
                  lat: { type: "number", description: "Latitud de la foto si tiene" },
                  lng: { type: "number", description: "Longitud de la foto si tiene" },
                  timestamp: { type: "number", description: "Timestamp de la foto en milisegundos" },
                  gpsAccuracy: { type: "number", description: "Precisión de la señal de GPS" },
                  direction: { type: "number", description: "Dirección de la brújula de la cámara en grados" },
                  visionLabels: {
                    type: "array",
                    items: {
                      type: "object",
                      properties: {
                        name: { type: "string" },
                        isLandmark: { type: "boolean" }
                      }
                    }
                  },
                  ocrText: { type: "string", description: "Texto extraído de la foto" }
                },
                required: ["id"]
              }
            }
          },
          required: ["photos"]
        }
      }
    ]
  };
});

// Helper to mock the Express response object
function createMockResponse() {
  let responseData = null;
  let statusCode = 200;
  
  return {
    get data() {
      return responseData;
    },
    get statusCode() {
      return statusCode;
    },
    status(code) {
      statusCode = code;
      return this;
    },
    json(data) {
      responseData = data;
      return this;
    },
    send(data) {
      responseData = data;
      return this;
    },
    setHeader() {
      return this;
    }
  };
}

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "find_poi") {
      const { lat, lng, radius, keywords } = args;
      const req = {
        method: "POST",
        body: { lat, lng, radius, keywords }
      };
      const res = createMockResponse();

      await findPoiHandler(req, res);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(res.data, null, 2)
          }
        ]
      };
    } 
    
    else if (name === "analyze_exif") {
      const { filePath } = args;
      const absolutePath = path.resolve(filePath);
      
      if (!fs.existsSync(absolutePath)) {
        throw new Error(`El archivo de imagen no existe en la ruta especificada: ${absolutePath}`);
      }

      const fileBuffer = fs.readFileSync(absolutePath);
      
      // Parse with exifr
      const exifData = await exifr.parse(fileBuffer, {
        gps: true,
        exif: true,
        xmp: true,
        iptc: true
      });

      if (!exifData) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                lat: null,
                lng: null,
                timestamp: null,
                gps_accuracy: null,
                direction: null,
                message: "No se encontraron metadatos EXIF"
              }, null, 2)
            }
          ]
        };
      }

      // Convert coordinate components if any (exifr usually handles decimals natively)
      const lat = exifData.latitude || exifData.GPSLatitude || null;
      const lng = exifData.longitude || exifData.GPSLongitude || null;
      const timestamp = exifData.DateTimeOriginal || exifData.CreateDate || exifData.DateTime || null;
      const gps_accuracy = exifData.GPSHPositioningError || null;
      const direction = exifData.GPSImgDirection || null;

      const response = {
        lat: lat ? Number(lat) : null,
        lng: lng ? Number(lng) : null,
        timestamp: timestamp ? String(timestamp) : null,
        gps_accuracy: gps_accuracy ? String(gps_accuracy) : null,
        direction: direction ? Number(direction) : null
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response, null, 2)
          }
        ]
      };
    } 
    
    else if (name === "analyze_image") {
      const { filePath } = args;
      const absolutePath = path.resolve(filePath);

      if (!fs.existsSync(absolutePath)) {
        throw new Error(`El archivo de imagen no existe en la ruta especificada: ${absolutePath}`);
      }

      const fileBuffer = fs.readFileSync(absolutePath);
      const base64Image = fileBuffer.toString("base64");

      const req = {
        method: "POST",
        body: { image_base64: base64Image }
      };
      const res = createMockResponse();

      await analyzeImageHandler(req, res);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(res.data, null, 2)
          }
        ]
      };
    } 
    
    else if (name === "resolve_puzzle") {
      const { photos } = args;
      const req = {
        method: "POST",
        body: { photos }
      };
      const res = createMockResponse();

      await resolvePuzzleHandler(req, res);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(res.data, null, 2)
          }
        ]
      };
    } 
    
    else {
      throw new Error(`Herramienta no implementada o desconocida: ${name}`);
    }
  } catch (error) {
    return {
      isError: true,
      content: [
        {
          type: "text",
          text: `Error ejecutando herramienta ${name}: ${error.message}\nStack: ${error.stack}`
        }
      ]
    };
  }
});

// Run stdio transport connection
async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // Logs in MCP should be outputted to stderr, since stdout is used for JSON-RPC
  console.error("Reverse Geocoding MCP Server is running cleanly on stdio.");
}

run().catch((error) => {
  console.error("Critical error starting Reverse Geocoding MCP Server:", error);
  process.exit(1);
});
