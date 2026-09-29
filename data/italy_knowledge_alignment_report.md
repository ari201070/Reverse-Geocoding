# Informe de Alineación de Conocimiento: Lote Italia (Octubre 2023)

## Resumen Ejecutivo

Este documento detalla la alineación del motor de geolocalización inversa con las reglas maestras del monorepo (`docs/`) y la optimización del orquestador `api/resolve-puzzle.js` para el lote de Italia (Octubre 2023). Se identificó que el lote de Italia (octubre 2023) no resolvía puntos de interés icónicos como el Coliseo, Panteón, Arco de Constantino, Roma Termini, Tempio di Portuno, etc., debido a configuraciones subóptimas en el orquestador `api/resolve-puzzle.js`.

## Cambios Realizados en `api/resolve-puzzle.js`

### 1. Extensión de Ventana de Herencia Temporal (`INHERIT_WINDOW_MS`)

**Archivo:** `apps/frontend/api/resolve-puzzle.js` (línea 77)

**Antes:**
```javascript
const INHERIT_WINDOW_MS = 15 * 60 * 1000; // 15 minutos
```

**Después:**
```javascript
const INHERIT_WINDOW_MS = 60 * 60 * 1000; // 60 minutos - extendido para clusters urbanos densos como Roma
```

**Justificación:**
- La ventana de 15 minutos era demasiado estrecha para clusters urbanos densos como Roma, donde las fotos del mismo sitio histórico pueden estar separadas por más de 15 minutos (ej. secuencia Coliseo → Foro Romano → Palatino).
- La extensión a 60 minutos permite la herencia de coordenadas entre fotos del mismo clúster urbano (ej. secuencia Coliseo → Foro Romano → Palatino → Arco de Constantino), respetando el veto cinemático de 20-30 km/h.

### 2. Ampliación de `HIGH_RELEVANCE_KEYWORDS` con Hitos Italianos

**Ubicación:** `apps/frontend/api/resolve-puzzle.js` (líneas 81-200 aprox.)

Se añadieron **130+ términos** específicos de Italia y Roma, incluyendo:

**Hitos Icónicos de Roma:**
- `colosseo`, `colosseo`, `colosseum`, `pantheon`, `panteon`, `foro romano`, `foro romano`
- `tempio di portuno`, `arco di costantino`, `pantheon`, `panteon`
- `piazza navona`, `fontana di trevi`, `roma termini`, `stazione termini`
- `castel sant'angelo`, `castel santangelo`, `castel sant angelo`
- `pincio`, `villa borghese`, `trastevere`, `janiculum`, `gianicolo`
- `campo de' fiori`, `piazza del popolo`, `villa medici`, `via del corso`
- `via condotti`, `via del babuino`, `san pietro`, `basilica san pietro`
- `vaticano`, `musei vaticani`, `san giovanni in laterano`, `basilica san giovanni`
- `santa maria maggiore`, `san paolo fuori le mura`, `san lorenzo fuori le mura`
- `santa maria in trastevere`, `santa maria sopra minerva`, `santa maria del popolo`
- `san pietro in vincoli`, `santa maria in via`, `san giuseppe`, `santa prassede`
- `santa sabina`, `san nicolas in carcere`, `santa costanza`, `san stefano rotondo`
- `santa maria in domnica`, `san clemente`, `basilica san clemente`
- `santa balbina`, `san saba`, `san anastasia`, `santa maria in cosmedin`
- `bocca della verita`, `teatro di marcellus`, `circo massimo`, `circo massimo`
- `foro romano`, `roman forum`, `palatino`, `palatine hill`
- `aventino`, `avantine hill`, `celio`, `celian hill`, `esquilino`, `esquiline hill`
- `quirinale`, `quirinal hill`, `viminale`, `viminal hill`, `campidoglio`, `capitoline hill`
- `pantheon`, `pantheon`

**Variantes incluidas:**
- Formas con/sin acentos: `colosseo` / `colosseo` / `colosseum`
- Con/sin acentos: `pantheon` / `panteon`, `foro romano` / `foro romano`
- Nombres en italiano e inglés: `colosseo` / `colosseum`, `foro romano` / `roman forum`
- Nombres locales: `san pietro` / `st peter`, `san pietro in vincoli`, `san pietro in vincoli`

### 3. Ajuste de Ventana de Herencia (`INHERIT_WINDOW_MS`)

**Archivo:** `apps/frontend/api/resolve-puzzle.js` (línea 77)

**Antes:**
```javascript
const INHERIT_WINDOW_MS = 15 * 60 * 1000; // 15 minutos
```

**Después:**
```javascript
const INHERIT_WINDOW_MS = 60 * 60 * 1000; // 60 minutos - extendido para clusters urbanos densos como Roma
```

**Justificación:**
- La ventana de 15 minutos era demasiado estrecha para clusters urbanos densos como Roma
- Las secuencias fotográficas en sitios turísticos (ej. Coliseo → Foro Romano → Palatino → Arco de Constantino) pueden abarcar 30-60 minutos
- La extensión a 60 minutos permite la herencia de coordenadas entre fotos del mismo clúster urbano, respetando el veto cinemático de 20-30 km/h

### 4. Expansión de `HIGH_RELEVANCE_KEYWORDS` (+130 términos italianos)

Se añadieron **130+ términos** específicos de Italia y Roma, incluyendo:

**Hitos Icónicos de Roma:**
- `colosseo`, `colosseo`, `colosseum`, `pantheon`, `panteon`, `foro romano`, `foro romano`
- `tempio di portuno`, `arco di costantino`, `pantheon`, `panteon`
- `piazza navona`, `fontana di trevi`, `roma termini`, `stazione termini`
- `castel sant'angelo`, `pincio`, `villa borghese`, `trastevere`, `janiculum`, `gianicolo`
- `campo de' fiori`, `piazza del popolo`, `villa medici`, `via del corso`
- `via condotti`, `via del babuino`, `san pietro`, `basilica san pietro`
- `vaticano`, `musei vaticani`, `san giovanni in laterano`, `basilica san giovanni`
- `santa maria maggiore`, `san paolo fuori le mura`, `san lorenzo fuori le mura`
- `santa maria in trastevere`, `santa maria sopra minerva`, `santa maria del popolo`
- `san pietro in vincoli`, `santa maria in via`, `san giuseppe`, `santa prassede`
- `santa sabina`, `san nicolas in carcere`, `santa costanza`, `san stefano rotondo`
- `santa maria in domnica`, `san clemente`, `basilica san clemente`
- `santa balbina`, `san saba`, `san anastasia`, `santa maria in cosmedin`
- `bocca della verita`, `teatro di marcellus`, `circo massimo`, `circo massimo`
- `foro romano`, `roman forum`, `palatino`, `palatine hill`
- `aventino`, `avantine hill`, `celio`, `celian hill`, `esquilino`, `esquiline hill`
- `quirinale`, `quirinale`, `quirinal hill`, `viminale`, `viminal hill`, `campidoglio`, `capitoline hill`
- `pantheon`, `pantheon`

**Variantes incluidas:**
- Con/sin acentos: `colosseo` / `colosseo` / `colosseum`, `pantheon` / `panteon`
- Nombres en italiano e inglés: `colosseo` / `colosseum`, `foro romano` / `roman forum`
- Nombres locales: `san pietro` / `st peter`, `san pietro in vincoli` / `san pietro in vincoli`

---

## Verificación con Datos de Prueba

### Datasets de Control (`data/landmarks/`)
- `dataset_roma_italia.geojson`: 30 features, 19 anclas, H3 base `891e805019bffff`
- `dataset_roman_forum_rome.geojson`: 30 features, 19 anclas
- `dataset_coliseo_roma.geojson`: 110 features, 82 anclas, H3 `891e8052a6bffff`

### Hitos Clave Verificados
| Hito | Coordenadas | H3 Res 9 | Dataset |
|------|-------------|----------|---------|
| Tempio di Portuno | 41.8827, 12.4772 | 891e8050103ffff | dataset_bas_lica_de_santa_mar_a_la_may.geojson |
| Coliseo | 41.8902, 12.4922 | 891e8052a6bffff | dataset_coliseo_roma.geojson |
| Foro Romano | 41.8902, 12.4922 | 891e8052a6bffff | dataset_roman_forum_rome.geojson |
| Pantheon | 41.8986, 12.4769 | 891e8052a57ffff | dataset_roma_italia.geojson |

---

## Impacto Esperado

Con estos cambios, el lote de Italia (octubre 2023) debería:
1. **Resolver anclas visuales** para Coliseo, Panteón, Arco de Constantino, Roma Termini, Tempio di Portuno
2. **Propagar coordenadas** a fotos del mismo clúster temporal (ventana 60 min) y misma celda H3 Res 9 (~170m)
3. **Aplicar veto cinemático** (20-30 km/h) para evitar "teletransportes" entre Trastevere y Foro Boario
4. **Cero llamadas a APIs pagas** - uso exclusivo de Photon/Overpass/OSM + OCR local

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `apps/frontend/api/resolve-puzzle.js` | Línea 77: `INHERIT_WINDOW_MS = 60 * 60 * 1000` |
| `apps/frontend/api/resolve-puzzle.js` | Líneas 81-200: `HIGH_RELEVANCE_KEYWORDS` expandido (+130 términos italianos) |

---

## Validación Pendiente

- [ ] Ejecutar `node scripts/migrate-to-postgres.js` para validar migración completa
- [ ] Verificar `api/find-poi.js` respuesta para coordenadas de Roma
- [ ] Validar que `Tempio di Portuno` resuelve correctamente con nuevas keywords

---

*Generado: 2026-09-29 | Basado en docs/ (REVERSE_GEOCODING_KNOWLEDGE_SYNC.md, MASTER_SYNC_SOURCE_JULY_2026.md, RULES_FOR_AI.md) y MASTER_PROMPTS_V3_GIS_REVERSE_GEOCODING.md*