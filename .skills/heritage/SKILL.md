# Skill: Modo Puzzle y Herencia

## Objetivo
Propagar la identidad resuelta de la "Foto Ancla" al resto del lote de fotos.

## Concepto de Foto Ancla

La **Foto Ancla** es la piedra angular del sistema:
- Primera foto del lote que se resuelve exitosamente
- Sirve como referencia para todas las demás fotos
- Analogía: pieza central de un rompecabezas

## Condiciones de Herencia

| Condición | Valor | Notas |
|-----------|-------|-------|
| **Tiempo** | ≤ 15 minutos (900s) | Diferencia EXIF entre fotos |
| **Espacio** | Misma celda H3 Res 9 | ~170m de diámetro |

## Selección del Mejor Ancla

Cuando múltiples fotos pueden ser ancla, prioriza:

1. **Mayor score**: LANDMARK (1.0) > OCR_SHORT (0.8) > OCR_LONG (0.4) > GPS_ONLY (0.2)
2. **Menor GPS accuracy**: tie-breaker si scores iguais
3. ** Menor timestamp**: primera del lote

```javascript
// De api/resolve-puzzle.js
const sortedAnchors = scoredPhotos
    .filter(p => p.score > 0)
    .sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        return a.accuracy - b.accuracy;  // Tie-break
    });

const masterAnchor = sortedAnchors[0];
```

## Propagación de Coordenadas

```javascript
// De api/resolve-puzzle.js - Phase 4
const INHERIT_WINDOW_MS = 15 * 60 * 1000; // 15 min

const results = photos.map(photo => {
    const isAnchor = photo.id === masterAnchor?.id;
    const timeDiff = masterTimestamp ? Math.abs(photo.timestamp - masterTimestamp) : Infinity;
    const canInherit = timeDiff <= INHERIT_WINDOW_MS;

    return {
        evidence: isAnchor ? 'ANCHOR_PHOTO' : (canInherit ? 'TIME_PROXIMITY' : 'INDIVIDUAL'),
        lat: photo.lat || (canInherit ? masterLat : null),
        lng: photo.lng || (canInherit ? masterLng : null)
    };
});
```

## Ancla: Datos Almacenados

```python
datos_ancla = {
    'foto_id': 'uuid',
    'es_ancla': True,
    'metodo_validacion': 'LANDMARK' | 'OCR' | 'GPS',
    'confianza': score,
    '_lat': -34.6037,
    'lon': -58.3816,
    'h3_index': '892834akerfffff',
    'nombre_lugar': 'El Boliche de Nico'
}
```

## Casos Edge

| Escenario | Manejo |
|-----------|--------|
| Sin fotos válidas | Crear ancla vacía, cada foto requiere validación propia |
| Múltiples anclas | Seleccionar por mayor confianza, otras como backup |
| Ancla con baja confianza | No propagar, requerir revisión humana |
| Fotos en diferentes celdas H3 | Cada celda tiene su propio ancla |

## Beneficios del Modo Puzzle

- **Ahorro de API**: 1 llamada OCR = 5-10 fotos resueltas
- **Velocidad**: Herencia ~0.1ms
- **Consistencia**: Mismas coordenadas para fotos del mismo lugar
- **Resiliencia**: Si falla OCR en foto B, puede heredar de foto A
- **Costo**: 80-90% ahorro en geocodificación

## Referencias
- [11] Herencia y modo puzzle