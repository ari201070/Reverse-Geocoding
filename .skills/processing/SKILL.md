# Skill: Reconciliación con RapidFuzz

## Objetivo
Unir fragmentos de texto detectados por OCR para confirmar el nombre oficial del lugar.

## Algoritmo: Token Set Ratio

RapidFuzz usa el algoritmo Token Set Ratio para fuzzy string matching:
1. **Tokenización**: Dividir strings en tokens individuales
2. **Ordenamiento**: Ordenar tokens alfabéticamente
3. **Conjuntos**: Calcular intersección/union de sets
4. **Score**: 2 * |intersección| / |set1| + |set2|

## Ejemplo Práctico

```
Fragmento 1: "Boliche"
Fragmento 2: "Nico"
Resultado: "Boliche Nico" → match ~75% con "El Boliche de Nico"
```

## Parámetros

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| score_cutoff | 70 | Umbral mínimo para match válido |
| threshold | 60 | Longitud máxima para OCR_SHORT |

## Código de Referencia

```python
# De documentation
from rapidfuzz import fuzz

fragmento_1 = "Boliche"
fragmento_2 = "Nico"
resultado = fuzz.token_set_ratio(fragmento_1, fragmento_2)
# Retorna score 0-100
```

## Fallback: Ollama Cleanup

Para OCR_LONG (≥60 chars), usar Ollama (phi3) para limpiar:
- 输入: Texto OCR largo
- Output: Nombre limpio del lugar

```javascript
// De api/resolve-puzzle.js - Phase 2
if (masterAnchor?.type === 'OCR_LONG') {
    const ollamaRes = await fetch('http://localhost:3000/api/ollama', {
        model: 'phi3',
        prompt: `Eres un experto en geolocalización. Dado el siguiente texto, identifica el NOMBRE DEL LUGAR. Si no puedes, responde 'Desconocido'. Solo responde el nombre o 'Desconocido'.`
    });
}
```

## Referencias
- [5] Sistema de reconciliación