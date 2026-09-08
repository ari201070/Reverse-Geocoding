# NOTAS: Reverse-Geocoding Master Knowledge Base

> **FUENTE**: Consolidado de 49 fuentes de NotebookLM — Guardado para referencia futura
> **ÚLTIMA ACTUALIZACIÓN**: 2026-04-14

---

## 📊 PRICING APIs 2026 (Resumen)

| Provider | Free Tier | $/k req | Almacenamiento |
|---------|-----------|---------|---------------|
| Google Maps | 10k/mes | $5.00 | ❌ Prohibido (30 días máx) |
| HERE | 1k/día | ~$0.75 | ✅ Permitido |
| Mapbox | 100k/mes | $5.00 | ⚠️ Solo API Permanente |
| **OpenCage** | 2.5k/día | ~$0.50 | ✅ Libre (sin restricciones) |
| Geoapify | 3k/día | $59/mes (100k) | ✅ Permitido |
| Nominatim | ∞ (self) | $0 | ✅ Total |

**RECOMENDACIÓN**: OpenCage (N2) → Google Places (N3) → PostGIS H3 (N1)

---

## 🔄 BEST PRACTICES CACHING (Case Study Rover)

### CLAVE: NO usar coordenadas exactas
- Precisión 4 decimales (~10m) = cache misses excesivos
- Usar **H3 Index** o **Geohash** para agrupar

### Resolución H3 Recomendada

| Res | Precisión | Hit Ratio | Uso |
|-----|-----------|-----------|-----|
| 6 | ~1.2km | 80% | Rural disperso |
| **7** | **~150m** | **78%** | **Óptimo urbano** |
| 8 | ~43m | 72% | Alta precisión |
| **9** | **~11m** | **65%** | **Tu sistema** |

### Anti-Contaminación
```javascript
function isValidCoordinate(lat, lng) {
  return lat >= -90 && lat <= 90 &&
         lng >= -180 && lng <= 180 &&
         !(lat === 0 && lng === 0) &&
         !isNaN(lat) && !isNaN(lng);
}
```

### Benchmark H3 vs Trigonométricos
| Método | 1M lugares | Speedup |
|-------|-----------|---------|
| Trigonométrico | 1500ms | 1x |
| **H3 B-Tree** | **0.1ms** | **15,000x** |

---

## 🎓 INSIGHTS ACADÉMICOS

### Benchmarks de Precisión

| Entorno | Éxito Rooftop | Error Típico |
|---------|---------------|--------------|
| Urbano | 70-90% | ±15-50m |
| Suburbano | 60-80% | ±50-100m |
| Rural | 40-60% | ±100-200m |

### Niveles de Precisión Estándar
1. **Rooftop** (oro) → ±10-50m
2. **Address Point** → ±15-30m
3. **Street Interpolation** → ±50-200m (EVITAR)
4. **ZIP Centroid** → ±500m-1km

### Requisitos por Aplicación
- Salud/Epidemiología: <50m
- Clasificación industrial: <1500m
- Tu sistema (fotos): ~11m (4 decimales)

---

## 🏢 COMPARATIVA PROVEEDORES

### Google Maps
- ✅ Cobertura 99.9%, precisión máxima
- ❌ $5/k req, prohibido guardar, debe mostrar en mapa Google
- **Ideal**: Apps premium globales

### HERE Technologies
- ✅ Logística/automotive, límites peso/altura
- ❌ Pricing complejo, compromisos volumen
- **Ideal**: Gestión flotas, rutas entrega

### Mapbox
- ✅ 100k req/mes gratis, personalización visual
- ❌ "Efecto acantilado": salto directo a $5/k
- **Ideal**: Startups con UX diferenciador

### OpenCage ⭐ RECOMENDADO
- ✅ 2.5k/día gratis, guardar siempre, GDPR
- ❌ Precisión depende de OSM
- **Ideal**: Independencia proveedores, salud

### Nominatim
- ✅ Gratuito, ilimitado (self-hosted)
- ❌ API pública throttled, self-hosting costoso
- **Ideal**: Prototipos, hobby

---

## 🔒 HIPAA/GDPR COMPLIANCE

### HIPAA (USA)
- ❗ BAA obligatorio si procesas PHI
- ❗ SSL/HTTPS obligatorio
- ✅ Plan de contingencia obligatorio

### OpenCage HIPAA
- ✅ Empresa alemana (GDPR compliant)
- ✅ Parámetro `no_record`: No guarda logs
- ✅ Retención logs: 6 meses
- ✅ BAA disponible Enterprise

### Privacy Mode
```javascript
function anonymize(lat, lng, precision = 4) {
  const factor = Math.pow(10, precision);
  return {
    lat: Math.round(lat * factor) / factor,
    lng: Math.round(lng * factor) / factor
  };
}
```

### Niveles Anonimización
| Precisión | Área | Uso |
|-----------|------|-----|
| 2 decimales | ~1.1km | Agregación regional |
| 3 decimales | ~110m | Análisis urbano |
| **4 decimales** | **~11m** | **Tu sistema** |
| 5 decimales | ~1.1m | ⚠️ Evitar (ingeniería inversa) |

### Políticas Retención
| Dato | Retención | Razón |
|------|-----------|-------|
| GPS original | 0 (inmediato) | Minimización |
| GPS anonimizado | 30 días | Caché |
| Nombres lugares | Indefinido | Consentimiento |
| EXIF fecha | 90 días | Auditoría |

---

## 🗺️ DECISION MATRIX

```
¿Procesas PHI/datos salud?
├─ SÍ → OpenCage + no_record
└─ NO → ¿Priorizas soberanía?
        ├─ SÍ → OpenCage o Geoapify
        └─ NO → ¿Budget limitado?
                ├─ SÍ → Mapbox (<100k) o Nominatim
                └─ NO → Google Maps (precisión máx)
```

---

## 📋 CHECKLIST IMPLEMENTACIÓN

### Setup Inicial
- [ ] Configurar OpenCage API key
- [ ] Configurar Google Places API key
- [ ] Crear tabla PostGIS `known_places`
- [ ] Indexar con H3 Res 9

### Privacy
- [ ] Implementar anonymizeCoordinates()
- [ ] Configurar no_record en OpenCage
- [ ] Policy de retención de 30 días

### Monitoring
- [ ] Alertar si p95 > 500ms
- [ ] Alertar si hit rate < 70%
- [ ] Alertar si budget > 90%

---

## 🔗 FUENTES ORIGINALES (49)

### Pricing & Providers
- Radar, AWS Marketplace/HERE, Zyla API, Geocodio, CSV2GEO, Geoapify, Ambee, HERE Official

### Academic
- PMC: Error propagation models
- PubMed: Positional differences
- arXiv: Next-gen Geocoding

### Case Studies
- Rover Search: Caching at Scale

### Compliance
- OpenCage HIPAA, ArcGIS docs

### Technical
- PostGIS, Nominatim, Mapbox, GeoPy

---

*Conocimiento consolidado — Listo para implementar*
