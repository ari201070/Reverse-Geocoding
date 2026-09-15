# Informe de avances — Geocodificación local del catálogo

## Estado del catálogo (`data/photo_catalog.db`, 34.557 fotos)
- **Inicio**: 28.179 sin GPS (81%).
- **Fase A (ciudad)**: 4.045 vía Nominatim (8 ciudades, pacing 1,2 s).
- **Fase B (herencia ±15 min)**: 1.179.
- **Fase C (centroide de viaje)**: 4.394, de las cuales **1.946 revertidas**
  por anclas contaminadas (Bosnia/Croacia/Dinamarca/Creta) → neto 2.448.
- **Veto 120 km/h (auditoría)**: 411 marcadas, 194 coords falsas a NULL,
  217 a revisión manual.
- **Neto geolocalizado**: ~7.672. **Restantes**: ~20.500.

## Piloto carpeta F:\2008\11-Noviembre (41 archivos, 100%)
- Match por SHA-256: 41/41. Mini Israel 31.8423,34.9690 · Nafah 33.0575,35.7351
  · Akko centroide inicial → **refinado a 11 POIs** (El-Jazzar 32.9227,35.0704,
  Khan al-Umdan 32.9199,35.0691, Khan Eshuna, puerto, murallas…) con visión
  propia + Photon/Overpass/Nominatim.
- `.mov` heredado ±15 min. Tags GPS + XMP + IPTC + XP en archivos.

## Piloto F:\2008\12-Diciembre (86 archivos, 100%)
- Har Karkom 30.2883,34.7430 (pico Overpass) · Timna por sitio (arte rupestre,
  templo Hathor 29.7680,34.9564, Pilares 29.7690,34.9553) · Yotvata
  29.895,35.058 · Janucá como interior sin coords.

## Lecciones registradas
1. **Sin centroides gruesos** donde haya POIs distinguibles (Akko).
2. exiftool falla con MakerNotes corruptos → `-m` + GPS en XMP.
3. Taggear archivos **cambia su SHA-256**: re-emparejar por nombre después.
4. GeoImgr lee IPTC:Keywords/XPKeywords, no solo XMP:Subject.
5. Duplicados (`is_duplicate=1`): propagar desde `duplicate_of`.
6. VLM local: moondream devuelve eco/placebos; qwen2.5-vl:7b intusable en
   esta CPU (>10 min/foto). Visión del agente + FOSS rindió más.

## Herramientas VLM disponibles
Ollama: `moondream:latest` (1,7 GB), `qwen2.5-vl:7b` (6 GB, muy lento en
CPU), `llama3.2`, `qwen2.5-coder`, `gemma3/4`; Gemini API key (L4 manual);
tesseract.js (WASM, sin binario nativo); exiftool 13.59; piexif (fallback).
