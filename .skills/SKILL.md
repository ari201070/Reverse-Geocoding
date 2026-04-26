# Ingeniería Inversa Geográfica

## Resumen del Sistema

Sistema de geocodificación que reconstruye la "Verdad del Lugar" usando evidencia física, visual y semántica.

## Los 7 Pasos (Skills)

| # | Paso | Skill | Descripción |
|---|------|-------|-------------|
| 1 | Capture | SKILL-capture | Extraer EXIF y aplicar privacidad |
| 2 | Extracción | SKILL-extraction | OCR, Landmarks, Labels |
| 3 | Processing | SKILL-processing | RapidFuzz reconciliación |
| 4 | Análisis | SKILL-analysis | Micro-fisonomía, sincronización solar |
| 5 | Consenso | SKILL-consensus | Scoring + HITL |
| 6 | Persistence | SKILL-persistence |SpatialCache (PostGIS) |
| 7 | Heritage | SKILL-heritage | Propagación desde ancla |

## Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│                    1. CAPTURE                              │
│  Extrae EXIF (fecha, hora, GPS). Aplica Privacy Mode           │
│  - GPS original: eliminar tras conversión               │
│  - GPS 4 decimales (~11m): guardar 30 días              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    2. EXTRACTION                           │
│  Google Cloud Vision API                                    │
│  - TEXT_DETECTION: textos                                  │
│  - LANDMARK_DETECTION: monumentos                         │
│  - LABEL_DETECTION: objetos/mobiliario                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    3. PROCESSING                         │
│  RapidFuzz (Token Set Ratio)                              │
│  - Unir fragmentos: "Boliche" + "Nico" → "El Boliche..."  │
│  - Fallback: Ollama (phi3) para OCR_LONG >= 60 chars        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. ANALYSIS                          │
│  Micro-fisonomía + Sincronización Solar                  │
│  -识别 furniture, walls, bar type                       │
│  - Validar via sombras del sol                         │
│  - Construir memoria visual colective                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────��───────────────────────────────────┐
│                    5. CONSENSUS                            │
│  Scoring + Human-in-the-Loop                            │
│  - LANDMARK: 1.0 | OCR_SHORT: 0.8 | OCR_LONG: 0.4 | GPS: 0.2│
│  - confidence = (anchorScore * 0.7) + (consistency * 0.3) │
│  - threshold: 75% automático, < 75% → HITL              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    6. PERSISTENCE                        │
│  SpatialCache (PostGIS + H3)                            │
│  - H3 Resolución 9 (~170m)                             │
│  -Índice B-Tree: 0.1ms para 1M lugares                 │
│  - Coordenadas 4 decimales forzosas                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    7. HERITAGE                           │
│  Modo Puzzle - Propagación                             │
│  - Foto Ancla = mejor scoring                          │
│  - Herencia: < 15 min + misma celda H3                 │
│  - Propagar coordenadas a todo el lote               │
└─────────────────────────────────────────────────────────────┘
```

## Scoring Ponderado

| Tipo | Score | Threshold | Notes |
|------|-------|-----------|-------|
| LANDMARK | 1.0 | N/A | isLandmark=true |
| OCR_SHORT | 0.8 | < 60 chars | Mejor resultado |
| OCR_LONG | 0.4 | >= 60 chars | Requiere Ollama |
| GPS_ONLY | 0.2 | N/A | Fallback |
| NONE | 0.0 | N/A | Requiere validación |

## Thresholds

| Métrica | Valor | Acción |
|--------|------|--------|
| Confianza automática | >= 75% | Resolver automáticamente |
| Confianza revisión | 50-74% | Verificación requerida |
| Tiempo clustering | 60 min (3600s) | Nueva sesión |
| Tiempo herencia | 15 min (900s) | Propagar desde ancla |
| Precisión GPS | 4 decimales | Privacidad |
| H3 Resolución | 9 | ~170m |

## Referencias

- [4] Privacidad y compliance
- [5] Reconciliación RapidFuzz
- [6] Micro-fisonomía
- [7] Consenso y umbrales
- [8] HITL protocolo
- [9] PostGIS y SpatialCache
- [10] H3 indexing
- [11] Herencia y modo puzzle

## Skills Disponibles

```
.skills/
├── capture/SKILL.md
├── extraction/SKILL.md
├── processing/SKILL.md
├── analysis/SKILL.md
├── consensus/SKILL.md
├── persistence/SKILL.md
└── heritage/SKILL.md
```

---

*Sistema v3.2 - Ingeniería Inversa Geográfica*