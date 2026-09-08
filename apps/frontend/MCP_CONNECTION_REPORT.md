# Reporte de Diagnóstico: Fallo de Conexión de Servidores MCP

**Fecha:** 2025-07-12  
**Proyecto:** Travel-Booking-Document-Hub  
**Configuración:** `.mcp.json` → 3 servidores vía symlinks a Reverse-Geocoding

---

## Resumen Ejecutivo

**Los servidores NO se conectan porque la arquitectura de symlinks rompe la resolución de dependencias y rutas relativas.** Cada servidor MCP está diseñado para ejecutarse desde SU propido directorio con SU propio `node_modules` y `.env`. Al ejecutarlos via symlinks desde `Travel-Booking-Document-Hub`, se rompen:

1. **Rutas relativas** (`.env`, bases de datos, archivos de config)
2. **Resolución de módulos** (Node busca en `cwd()/node_modules`, no en el realpath del symlink)
3. **Contexto de proceso** (`process.cwd()` apunta al proyecto equivocado)

---

## Análisis por Servidor

### 1. `reverse-geocoding-api` (`./mcp-server/index.js`)

| Aspecto | Estado | Problema |
|---------|--------|----------|
| **Symlink** | ✅ Existe | `mcp-server → ../Reverse-Geocoding/mcp-server` |
| **package.json** | ❌ **Incompleto** | No declara `@modelcontextprotocol/sdk`, `exifr`, `dotenv` como dependencies |
| **node_modules** | ✅ Existe localmente | Pero no se usa al ejecutar desde symlink |
| **Carga .env** | ❌ **Rota** | `path.resolve(__dirname, "..", ".env")` → busca en `Reverse-Geocoding/.env`, no en `Travel-Booking-Document-Hub/.env` |
| **DB photo_catalog** | ❌ **Rota** | Ruta hardcodeada: `'C:\\Users\\flier\\.gemini\\antigravity\\scratch\\photo_catalog.db'` |

### 2. `photo-catalog` (`./mcp-photo-catalog/dist/index.js`)

| Aspecto | Estado | Problema |
|---------|--------|----------|
| **Symlink** | ✅ Existe | `mcp-photo-catalog → ../Reverse-Geocoding/mcp-photo-catalog` |
| **package.json** | ✅ Correcto | Tiene sus dependencies declaradas |
| **Build (dist/)** | ✅ Existe | Compilado correctamente |
| **node_modules** | ❌ **No se usa** | Al ejecutar `node ./mcp-photo-catalog/dist/index.js` desde `Travel-Booking-Document-Hub`, Node resuelve módulos desde `Travel-Booking-Document-Hub/node_modules` (que NO tiene `@modelcontextprotocol/sdk`, `better-sqlite3`) |

### 3. `notebooklm` (`./notebooklm-mcp/dist/index.js`)

| Aspecto | Estado | Problema |
|---------|--------|----------|
| **Symlink** | ✅ Existe | `notebooklm-mcp → ../notebooklm-mcp` |
| **package.json** | ✅ Correcto | Dependencies declaradas |
| **Build (dist/)** | ✅ Existe | Compilado |
| **Autenticación** | ❌ **Rota** | Guarda cookies/sesión en `~/.config/notebooklm-mcp/` o similar; al ejecutar desde otro cwd, puede fallar al encontrar perfil de navegador |
| **node_modules** | ❌ **No se usa** | Mismo problema que photo-catalog |

---

## Causa Raíz Técnica

```json
// .mcp.json actual - EJECUCIÓN DESDE DIRECTORIO EQUIVOCADO
"reverse-geocoding-api": {
  "command": "node",
  "args": ["--no-warnings", "./mcp-server/index.js"]  // cwd = Travel-Booking-Document-Hub
}
```

**Cuando Node ejecuta un symlink:**
- `process.cwd()` = `C:\Users\flier\GitHub\Travel-Booking-Document-Hub`
- `import.meta.url` / `__dirname` = ruta REAL del archivo (resuelve symlink)
- **`require.resolve()` / `import` buscan en `cwd()/node_modules` → FALLAN**

---

## Soluciones Recomendadas

### Opción A: Copiar (no linkear) cada servidor MCP completo

```bash
# En Travel-Booking-Document-Hub
rm -rf mcp-server mcp-photo-catalog notebooklm-mcp
cp -r ../Reverse-Geocoding/mcp-server ./mcp-server
cp -r ../Reverse-Geocoding/mcp-photo-catalog ./mcp-photo-catalog
cp -r ../notebooklm-mcp ./notebooklm-mcp

# Instalar deps en cada uno
cd mcp-server && npm install
cd ../mcp-photo-catalog && npm install
cd ../notebooklm-mcp && npm install
```

### Opción B: Usar `command` con `cwd` explícito (si el cliente MCP lo soporta)

```json
{
  "mcpServers": {
    "reverse-geocoding-api": {
      "command": "node",
      "args": ["--no-warnings", "index.js"],
      "cwd": "C:/Users/flier/.gemini/antigravity/scratch/Reverse-Geocoding/mcp-server",
      "env": { "NODE_NO_WARNINGS": "1" }
    },
    "photo-catalog": {
      "command": "node",
      "args": ["--no-warnings", "dist/index.js"],
      "cwd": "C:/Users/flier/.gemini/antigravity/scratch/Reverse-Geocoding/mcp-photo-catalog",
      "env": { "NODE_NO_WARNINGS": "1" }
    },
    "notebooklm": {
      "command": "node",
      "args": ["--no-warnings", "dist/index.js"],
      "cwd": "C:/Users/flier/.gemini/antigravity/scratch/notebooklm-mcp",
      "env": { "NODE_NO_WARNINGS": "1" }
    }
  }
}
```

### Opción C: Publicar como paquetes npm locales (`npm link` o `npm pack`)

```bash
# En cada servidor MCP
cd mcp-server && npm link
cd mcp-photo-catalog && npm link
cd notebooklm-mcp && npm link

# En Travel-Booking-Document-Hub
npm link reverse-geocoding-mcp mcp-photo-catalog notebooklm-mcp
```

Y en `.mcp.json`:
```json
"reverse-geocoding-api": { "command": "npx", "args": ["reverse-geocoding-mcp"] }
```

---

## Acciones Inmediatas Requeridas

1. **Corregir `mcp-server/package.json`** - Agregar dependencies faltantes
2. **Elegir una opción** (A, B o C) y aplicarla
3. **Verificar variables de entorno** - Cada servidor necesita su `.env` accesible desde su `cwd`
4. **Probar conexión** - Reiniciar cliente MCP (Claude Desktop / VS Code / etc.)

---

**Generado automáticamente por análisis de arquitectura MCP.**  
Para implementar la corrección, consultar al Arquitecto con este reporte como contexto.