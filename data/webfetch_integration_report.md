# Informe Técnico de Integración: WebFetch y Enriquecimiento de Metadatos

**Proyecto:** Reverse-Geocoding Local Infrastructure  
**Entorno:** Monorrepo Nativo (Windows) — Node.js + Python + SQLite (`photo_catalog.db`)  
**Estado:** Confirmado e Impactado  

---

## 1. Arquitectura de la Solución

El objetivo de esta integración es conectar de forma determinista el agente local a internet mediante el protocolo **MCP (Model Context Protocol)**. El flujo de datos se estructura en tres capas nativas dentro del monorrepo:

1. **Orquestación e Ingesta (Capa Agente):** El agente utiliza la extensión `WebFetch` para resolver desafíos, validar repositorios de GitHub, extraer URLs de comprobantes y scrapear comercios (hoteles/restaurantes), purificando el HTML basura a Markdown limpio.
2. **Persistencia (Capa Datos):** Sincronización intermedia mediante la tabla centralizada `spatial_cache` y la columna `voucher_url` en `photos` dentro de `photo_catalog.db` (SQLite).
3. **Automatización Física (Capa Scripting):** Procesamiento mediante `sync_exif_october_stayopen.py` para inyectar la URL validada en el campo `-XMP-xmp:BaseURL` de las imágenes `.jpg`.

---

## 2. Configuración del Entorno de Infraestructura (`.agent/`)

Archivo **`.agent/mcp-config.json`**:

```json
{
  "mcpServers": {
    "webfetch": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-fetch"
      ],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

---

## 3. Definición de Habilidad del Agente (`.skills/webfetch-enrich.json`)

Archivo **`.skills/webfetch-enrich.json`** registrado con pipeline de 3 pasos: validación, persistencia y automatización física con `-XMP-xmp:BaseURL`.

---

## 4. Automatización en Python (`sync_exif_october_stayopen.py`)

- Soporte nativo para lectura de `voucher_url` desde SQLite.
- Inyección física del tag `-XMP-xmp:BaseURL` mediante `ExifTool` junto a `GPSLatitude`, `GPSLongitude`, `ImageDescription` y `UserComment` (H3 Res 9).
- Flags mandatorios: `-overwrite_original` y `-m`.
