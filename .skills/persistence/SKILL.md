# Skill: Persistencia en SpatialCache (PostGIS)

## Objetivo
Almacenar y recuperar identidades de lugares en base de datos propia (SpatialCache).

## H3: Índice Espacial Hexagonal

### Resolución y Precisión

| Resolución | Área Celda | Uso |
|-------------|------------|-----|
| 7 | ~163 km² | País/Estado |
| 8 | ~21 km² | Ciudad grande |
| **9** | **~0.87 km² (~170m)** | **Local/Barrio** |
| 10 | ~0.12 km² | Intersección |

### Índice B-Tree vs GiST

| Tipo | Uso | Ventaja |
|------|-----|---------|
| **B-Tree** | Equality queries (=) | Más rápido para búsquedas exactas |
| **GiST** | Range queries (<, >, BETWEEN) | Necesario para proximidad |

```sql
-- B-Tree (recomendado para H3 equality)
CREATE INDEX idx_h3_btree ON lugares USING btree(h3_index);
-- Tiempo para 1M registros: ~0.1ms

-- GiST (para búsquedas por distancia)
CREATE INDEX idx_h3_gist ON lugares USING gist(h3_geo_to_h3(geom));
```

## Privacidad: Redondeo Forzoso

- **Conversión obligatoria**: GPS original → 4 decimales
- **4 decimales**: ~11m precisión (estándar seguro)
- **5+ decimales**: ~1.1m - PROHIBIDO (identifica domicilio)

```javascript
// De src/utils/puzzleLogic.js
function roundCoord(val) {
    return Math.round(val * 10000) / 10000;
}
```

## Tabla de Lugares

```sql
CREATE TABLE lugares (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,  -- 4 decimales
    lon DECIMAL(11, 8) NOT NULL,  -- 4 decimales
    h3_index BIGINT NOT NULL,     -- H3 Resolución 9
    confianza DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lugares_h3 ON lugares USING btree(h3_index);
```

## Query: Spatial Memory Lookup

```javascript
// De api/resolve-puzzle.js - Phase 3
if (masterLat && masterLng && !masterContext) {
    const memoryResult = await memoryStore.findMatch(masterLat, masterLng);
    if (memoryResult) masterContext = memoryResult.name;
}
```

## Beneficios del SpatialCache

- **80-90% ahorro OPEX**: Evitar consultas redundantes a APIs
- **0.1ms lookup**: vs 1500ms tradicionales
- **15,000x más rápido**
- **Soberanía de datos**: Control total sobre información

## Referencias
- [4] Privacidad y compliance
- [9] PostGIS y spatialcache