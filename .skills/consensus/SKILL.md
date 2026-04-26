# Skill: Consenso y Human-in-the-Loop (HITL)

## Objetivo
Determinar si la ubicación puede resolverse automáticamente o requiere intervención humana.

## Sistema de Scoring

| Tipo | Score | Longitud OCR | Notas |
|------|-------|-------------|-------|
| **LANDMARK** | 1.0 | N/A | Master clue - isLandmark=true |
| **OCR_SHORT** | 0.8 | < 60 chars | Mejor resultado |
| **OCR_LONG** | 0.4 | >= 60 chars | Requiere Ollama cleanup |
| **GPS_ONLY** | 0.2 | N/A | Fallback |
| **NONE** | 0.0 | N/A | Requiere validación |

## Fórmula de Confianza

```
confidence = (anchorScore * 0.7) + (consistencyBonus * 0.3)

Donde:
- anchorScore = score del mejor ancla (0.2 - 1.0)
- consistencyBonus = fotos con mismo nombre / total fotos
```

## Thresholds

| Confidence | Acción |
|------------|--------|
| ≥ 75% | Automático |
| 50-74% | Verificación requise |
| < 50% | Revisión humana |

## Tie-Breaker: GPS Accuracy

Cuando múltiples fotos tienen el mismo score, usar el de menor GPS accuracy:
```javascript
// De api/resolve-puzzle.js
sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.accuracy - b.accuracy;  // Lower is better
});
```

## Protocolo HITL

Si confidence < 75%:
1. Detener proceso automático
2. Invocar `request_user_validation`
3. Mostrar UI con opciones:
   - Confirmar resultado
   - Escribir nombre manualmente
   - Seleccionar otra foto como ancla

## Código de Referencia

```javascript
// De api/resolve-puzzle.js
const anchorScore = masterAnchor?.score || 0.1;
const consistencyBonus = results.filter(r => r.name && r.name === results[0]?.name).length / results.length;
const finalConfidence = Math.min(0.99, (anchorScore * 0.7) + (consistencyBonus * 0.3));

return {
    requiresManualValidation: finalConfidence < 0.75
};
```

## Referencias
- [7] Consenso y umbrales
- [8] HITL protocolo