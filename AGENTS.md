# Reglas pin para agentes (opencode)

1. **Consulta mandatoria al Arquitecto**: antes de redactar cualquier
   `implementation_plan.md` o abordar lógica compleja, invocar
   `consult_architect_llm` y alinear con la carpeta `REVERSE_GEOCODING` de
   NotebookLM (`docs/MASTER_PROMPTS_V3_GIS_REVERSE_GEOCODING.md`,
   `docs/NOTEBOOKLM_CONSOLIDATED_NOTES.md`). Sin excepciones, sin que el
   usuario lo recuerde.
2. **100% local primero**: caché H3 res 9 → Nominatim/Photon/Overpass →
   Ollama (`llama3.2`, `moondream`) → Gemini solo como último recurso.
3. **Fuente única de verdad**: `data/photo_catalog.db`. No crear ni usar
   copias. `PHOTO_CATALOG_DB` apunta ahí.
4. **Seguridad**: no commitear `.env`, claves ni `photo_catalog.db`-shm/wal.
   No borrar datos sin backup + confirmación del Arquitecto.
