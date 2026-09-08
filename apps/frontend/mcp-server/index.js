import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";
import exifr from "exifr";
import dotenv from "dotenv";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// 1. 🛡️ BLINDAJE GLOBAL: Redirigir de forma permanente todos los console.log a console.error
// Esto asegura que si algún archivo dentro de la carpeta /api o cualquier otra librería 
// intenta hacer un log, saldrá de forma segura por stderr sin romper el protocolo MCP.
console.log = console.error;

// 2. 🤫 Silenciar temporalmente process.stdout.write solo para la librería dotenv
const originalWrite = process.stdout.write;
process.stdout.write = () => true;

// Ejecutamos la carga del entorno
dotenv.config({ path: path.resolve(__dirname, "..", ".env"), quiet: true });

// Restauramos process.stdout.write inmediatamente para el canal JSON-RPC de MCP
process.stdout.write = originalWrite;

// Prompt oficial del Arquitecto de Reverse Geocoding
const ARCHITECT_SYSTEM_PROMPT = `Eres un Ingeniero de Software Senior y Arquitecto de Soluciones GIS especializado en Sistemas de Información Geográfica y optimización de APIs de Geolocalización. Actúas como el "Arquitecto de Reverse Geocoding" para el proyecto "Reverse Geocoding & Consensus Truth Engine".

Tus directivas de arquitectura obligatorias son:
1. Diseño Modular y Desacoplado: Divide tareas complejas (como inferencia de "Verdad del Lugar" o Azimut) en micro-módulos aislados y testeables paso a paso sin saturar la ventana de contexto del Agente Programador (AntiGravity).
2. Eficiencia de Datos y Soberanía Local (SpatialCache): Prioriza siempre la "Caché Espacial" local (como PostGIS/SQLite) y agrupamiento de coordenadas por índices hexagonales H3 (Resolución 9) antes de llamar a APIs externas pagadas (Google Maps, Cloud Vision). Si se resuelve en un hexágono, las consultas subsiguientes dentro de 15 minutos heredan la ubicación (tolerancia cero al desperdicio de peticiones de red).
3. Sinergia de Conocimiento (NotebookLM): Actúa como estratega de alto nivel. Para sintaxis exacta o documentación profunda de configuración, delega o indica consultar la "Fuente de Verdad" (NotebookLM) vía MCP.
4. Formato de Salida Interoperable: Toda interacción técnica DEBE finalizar obligatoriamente con un bloque claro, autocontenido y procesable etiquetado como "INSTRUCCIÓN PARA EL AGENTE" que el agente de IA (AntiGravity) pueda ejecutar directamente sin interpretación del usuario.

Tono de comunicación: Profesional, estratégico, enfocado en optimización de rendimiento y OPEX, y directo. Responde en Castellano.`;

// Helper para invocar la API de Gemini 2.5 de forma nativa con Failover a OpenRouter
async function callGeminiAPI(systemPrompt, userPrompt) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    console.error("No GEMINI_API_KEY configured. Skipping Gemini direct call.");
    return null;
  }
  const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;

  console.error("Intentando llamar a Gemini API nativa...");
  try {
    const response = await fetch(geminiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text: userPrompt }] }],
        systemInstruction: { parts: [{ text: systemPrompt }] },
        generationConfig: { temperature: 0.2, topP: 0.95, topK: 40, maxOutputTokens: 8192 }
      })
    });

    if (response.ok) {
      const result = await response.json();
      if (result.candidates?.[0]?.content?.parts?.[0]?.text) {
        console.error("✅ Conexión exitosa con la API de Gemini nativa.");
        return result.candidates[0].content.parts[0].text;
      }
    } else {
      console.error(`⚠️ Gemini API nativa retornó estado ${response.status}. Iniciando failover a OpenRouter...`);
    }
  } catch (error) {
    console.error(`⚠️ Error al llamar a Gemini API nativa: ${error.message}. Iniciando failover a OpenRouter...`);
  }

  // Fallback a OpenRouter
  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (!openRouterKey) {
    throw new Error("Ambos métodos fallaron: Gemini API nativa dio error de cuota/red y OPENROUTER_API_KEY no está configurada en .env.");
  }

  // Modelos preferidos de OpenRouter. Se lee del .env para evitar obsolescencia, con una lista resiliente por defecto.
  let openRouterModels = [
    "liquid/lfm-2.5-1.2b-instruct:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "openrouter/free",
    "google/gemini-2.5-flash:free"
  ];

  if (process.env.OPENROUTER_FALLBACK_MODELS) {
    openRouterModels = process.env.OPENROUTER_FALLBACK_MODELS.split(",").map(m => m.trim());
  }



  console.error("Intentando llamar a través de OpenRouter...");
  for (const model of openRouterModels) {
    try {
      console.error(`Intentando con modelo OpenRouter: ${model}...`);
      const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${openRouterKey}`,
          "HTTP-Referer": "https://localhost:3000",
          "X-Title": "Reverse Geocoding Architect Bridge"
        },
        body: JSON.stringify({
          model: model,
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt }
          ],
          temperature: 0.2
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.choices?.[0]?.message?.content) {
          console.error(`✅ Conexión exitosa con OpenRouter usando el modelo ${model}.`);
          return data.choices[0].message.content;
        }
      } else {
        const errDetail = await response.text();
        console.error(`⚠️ OpenRouter falló con modelo ${model} (status ${response.status}): ${errDetail}`);
      }
    } catch (err) {
      console.error(`⚠️ Error con modelo OpenRouter ${model}: ${err.message}`);
    }
  }

  throw new Error("Fallo crítico: No se pudo obtener respuesta de la API de Gemini nativa ni de OpenRouter.");
}


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
        description: "Encuentra puntos de interés (POIs) cercanos a coordenadas dadas utilizando una cascada FOSS (Caché local H3, Photon, Overpass, OpenCage).",
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
        description: "Analiza el contenido visual de una imagen local mediante cascada de visión gratuita (Gemini 2.5 Flash, OpenRouter) para extraer etiquetas, hitos y texto OCR.",
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
      },
      {
        name: "request_architecture_review",
        description: "Envía un fragmento de código y el problema arquitectónico al Arquitecto de Reverse Geocoding para obtener un diseño de desacoplamiento modular.",
        inputSchema: {
          type: "object",
          properties: {
            codigo_actual: { type: "string", description: "El fragmento o archivo de código actual que se desea revisar" },
            problema: { type: "string", description: "El problema técnico, desafío o pregunta arquitectónica específica" }
          },
          required: ["codigo_actual", "problema"]
        }
      },
      {
        name: "optimize_api_calls",
        description: "Envía un flujo o lógica de consumo de APIs de mapas/geolocalización al Arquitecto de Reverse Geocoding para obtener un diseño de optimización con PostGIS, H3 y caché espacio-temporal.",
        inputSchema: {
          type: "object",
          properties: {
            flujo_actual: { type: "string", description: "La lógica de negocio o código que consume APIs externas (por ejemplo, Google Maps, OpenCage)" }
          },
          required: ["flujo_actual"]
        }
      },
      {
        name: "ask_architect",
        description: "Realiza una consulta abierta sobre arquitectura GIS, patrones, optimización o decisiones de desarrollo al Arquitecto de Reverse Geocoding.",
        inputSchema: {
          type: "object",
          properties: {
            consulta: { type: "string", description: "La pregunta o consulta técnica para el Arquitecto" },
            contexto: { type: "string", description: "Información contextual relevante adicional (opcional)" }
          },
          required: ["consulta"]
        }
      },
      {
        name: "consult_architect_llm",
        description: "Permite enviar un prompt estructurado con código al Arquitecto cuando hay dudas sobre diseño de sistemas o errores complejos de lógica.",
        inputSchema: {
          type: "object",
          properties: {
            code: { type: "string", description: "El fragmento o archivo de código relevante para la consulta" },
            question: { type: "string", description: "La pregunta técnica o duda de diseño sobre el sistema" }
          },
          required: ["question"]
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
    
    else if (name === "request_architecture_review") {
      const { codigo_actual, problema } = args;
      const userPrompt = `CÓDIGO ACTUAL:\n\`\`\`javascript\n${codigo_actual}\n\`\`\`\n\nPROBLEMA / CONSULTA:\n${problema}`;
      const responseText = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
      
      return {
        content: [
          {
            type: "text",
            text: responseText
          }
        ]
      };
    }

    else if (name === "optimize_api_calls") {
      const { flujo_actual } = args;
      const userPrompt = `FLUJO ACTUAL DE LLAMADAS DE API:\n\`\`\`javascript\n${flujo_actual}\n\`\`\`\n\nPor favor, optimiza este flujo aplicando la lógica de Caché Espacial con índices hexagonales H3 (Resolución 9), herencia espacio-temporal, o bases de datos locales (PostGIS/SQLite). Proporciona los pasos exactos y el bloque "INSTRUCCIÓN PARA EL AGENTE" al final.`;
      const responseText = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
      
      return {
        content: [
          {
            type: "text",
            text: responseText
          }
        ]
      };
    }

    else if (name === "ask_architect") {
      const { consulta, contexto } = args;
      const userPrompt = `CONSULTA:\n${consulta}${contexto ? `\n\nCONTEXTO:\n${contexto}` : ""}`;
      const responseText = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
      
      return {
        content: [
          {
            type: "text",
            text: responseText
          }
        ]
      };
    }

    else if (name === "consult_architect_llm") {
      const { code, question } = args;
      const userPrompt = `CÓDIGO DE CONTEXTO:\n\`\`\`javascript\n${code || "No se proporcionó código."}\n\`\`\`\n\nPREGUNTA TÉCNICA / DUDA DE DISEÑO:\n${question}`;
      const responseText = await callGeminiAPI(ARCHITECT_SYSTEM_PROMPT, userPrompt);
      
      return {
        content: [
          {
            type: "text",
            text: responseText
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
