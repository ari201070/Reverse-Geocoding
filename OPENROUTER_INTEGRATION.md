# SDK Agéntico de OpenRouter

## Instalación

```bash
npm install openrouter-agent
```

## Configuración

```javascript
import { Agent } from 'openrouter-agent';

const agent = new Agent({
    apiKey: process.env.OPENROUTER_API_KEY,
    baseUrl: 'https://openrouter.ai/api/v1',
    model: 'anthropic/claude-3-sonnet'
});
```

## Uso en el Sistema de Geocodificación

### 1. Reconciliation de texto OCR largo

Cuando el OCR detecta más de 60 caracteres, OpenRouter puede limpiar y extraer el nombre del lugar:

```javascript
import { Agent } from 'openrouter-agent';

const agent = new Agent({
    apiKey: process.env.OPENROUTER_API_KEY,
    model: 'google/gemini-pro-1.5-flash'
});

async function limpiarOCR(textoOCR) {
    const response = await agent.complete(
        `Eres un experto en geolocalización. Dado el siguiente texto extraído de una foto por OCR, identifica el NOMBRE DEL LUGAR (ej: "Teatro Colón", "Rock & Feller's"). 
        
Si no puedes identificar un lugar específico, responde "Desconocido". 
Solo responde el nombre o "Desconocido". No agregues explicaciones.

Texto: "${textoOCR}"`
    );
    
    return response.text.trim();
}
```

### 2. Análisis de Micro-fisonomía

```javascript
async function analizarMicroFisonomia(imageBase64) {
    const response = await agent.completeWithImage(
        `Analiza esta imagen de un lugar y describe:
1. Tipo de mobiliario (sillas, mesas)
2. Estilo de decoración (paredes, iluminación)
3. Categoría probable del lugar (restaurante, café, bar)

Sé muy específico sobre detalles visuales.`,
        imageBase64
    );
    
    return response.text;
}
```

### 3. Validación de Consenso

```javascript
async function validarConsenso(fotos, resultadoActual) {
    const fotosInfo = fotos.map(f => 
        `- Foto ${f.id}: ${f.type} (score ${f.score})`
    ).join('\n');
    
    const response = await agent.complete(
        `Eres un experto en geocodificación. Given the following photos:
${fotosInfo}

Current consensus result: "${resultadoActual.place_name}" (confidence: ${resultadoActual.confidence})

Question: Does this result make sense? Reply YES or NO with a brief explanation.`
    );
    
    return response.text;
}
```

## Configuración con Variables de Entorno

```bash
# .env
OPENROUTER_API_KEY=sk-or-xxxxx
OPENROUTER_MODEL=anthropic/claude-3-sonnet
OPENROUTER_SITE_NAME=reverse-geocoding
OPENROUTER_SITE_URL=https://tu-dominio.com
```

## Integración con el API Existente

```javascript
// api/openrouter-service.js
import { Agent } from 'openrouter-agent';

export default async function (req, res) {
    const { prompt, image, model } = req.body;
    
    const agent = new Agent({
        apiKey: process.env.OPENROUTER_API_KEY,
        model: model || 'google/gemini-pro-1.5-flash'
    });
    
    let response;
    if (image) {
        response = await agent.completeWithImage(prompt, image);
    } else {
        response = await agent.complete(prompt);
    }
    
    return res.json({
        status: 'SUCCESS',
        response: response.text,
        usage: response.usage
    });
}
```

## Modelos Recomendados

| Modelo | Uso | Costo | Velocidad |
|--------|-----|-------|----------|
| google/gemini-pro-1.5-flash | OCR cleanup | Bajo | Rápido |
| anthropic/claude-3-sonnet | Análisis complejo | Medio | Medio |
| openai/gpt-4-turbo | Validación | Alto | Medio |

## Rate Limits

- Verificar límites en OpenRouter dashboard
- Implementar retry con backoff exponencial:

```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (e) {
            if (i === maxRetries - 1) throw e;
            await sleep(1000 * Math.pow(2, i)); // 1s, 2s, 4s
        }
    }
}
```