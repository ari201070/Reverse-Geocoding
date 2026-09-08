---
description: Workflow optimizado para desarrollo eficiente (Prompt -> Agent -> Prompt)
---

# Estrategia de Desarrollo Optimizado

Este workflow implementa las directrices de eficiencia para reducir pasos y tokens.

## 1. Fase de Prompt Inicial (Preparación)

Antes de invocar cambios complejos, define claramente el contexto y los criterios.

- **Checklist**:
  - [ ] ¿Es necesaria un agente o basta un prompt simple?
  - [ ] ¿Están claros los 3 problemas principales?
  - [ ] ¿Hay una condición de salida clara?
  - [ ] **Consulta al Arquitecto**: ¿Has consultado al Arquitecto del proyecto mediante `consult_architect_llm` para validar el diseño técnico, modularidad y optimización GIS/H3 alineándolo con la base de conocimientos de NotebookLM? *(Proceso fijo y mandatorio)*.


## 2. Fase de Agente (Ejecución Focalizada)

Ejecuta solo la parte difícil. No pidas "revisar todo el proyecto".

- **Acción**: Ejecutar cambios específicos.
- **Restricción**: Máximo 3-5 pasos.
- **Early Stop**: Si funciona, detenerse. No buscar perfección innecesaria.

// turbo

## 3. Fase de Prompt Final (Pulido)

Pulir, resumir y estructurar el resultado.

- Validar cambios.
- Generar resumen conciso.
