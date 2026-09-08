# Skill: Capture y Privacidad

## Objetivo
Extraer metadatos EXIF (fecha, hora, coordenadas) y aplicar Privacy Mode.

## Proceso

### 1. Extracción EXIF
- **Fuente**: Metadatos EXIF/XMP/IPTC de la imagen [4]
- **Datos**: fecha, hora, latitud, longitud, orientación del dispositivo
- **GPS**: Extraer coordenadas originales (≥5 decimales → ~1.1m precisión)

### 2. Privacy Mode
- **Conversión**: GPS original (5+ decimales) → 4 decimales (~11m)
- **Razón**: Estándar de seguridad - evita identificar domicilio exacto [4]
- **Prohibido**: 5+ decimales = permite identificar domicilio [4]

### 3. Retención de Metadatos
- **GPS original**: Eliminado inmediatamente tras conversión
- **GPS anonimizado (4 decimales)**: 30 días [4]
- **Metadatos temporales (fecha/orientación)**: 90 días para auditoría [4]
- **Nombres de lugares**: Indefinido (con consentimiento) [4]

## Código de Referencia

```javascript
// De src/utils/puzzleLogic.js
const H3_RESOLUTION = 9;  // ~170m hexágonos
const TIME_WINDOW_S = 3600;  // 60 min clustering

function roundCoord(val) {
    return Math.round(val * 10000) / 10000;  // 4 decimales = ~11m
}
```

## Thresholds

| Dato | Precisión | Retención | Acción |
|-----|-----------|----------|--------|
| GPS original | ~1.1m | 0 (inmediato) | Eliminar |
| GPS anonimizado | ~11m | 30 días | Guardar |
| EXIF fecha | N/A | 90 días | Auditoría |

## References
- [4] Privacidad y compliance de datos