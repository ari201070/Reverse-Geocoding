# REGLAS MAESTRAS PARA ANTIGRAVITY (ESTRATEGIA FUNCIONAL)

Copia el siguiente bloque y pégalo en tus "Instrucciones Personalizadas" (Custom Instructions) para asegurar este comportamiento.

---

## 🚀 MODO LEAN AGENT: ESTRATEGIA DE TOKENS

### ⚓ PROMPT ÁNCORA (Obligatorio en primer mensaje)

Cada vez que inicies un chat, pega esto:

> Follow these rules strictly:
>
> - Act as a lean agent
> - Minimize reasoning steps
> - Avoid self-reflection loops
> - Do not explore the project unless explicitly asked
> - Prefer direct answers over exploration

### 🧠 PROTOCOLO DE PROCESAMIENTO

1.  **Planning SIEMPRE**: El primer paso debe ser un Plan de Implementación (`implementation_plan.md`).
2.  **Thinking SOLO si falla**: No actives el razonamiento profundo a menos que la solución directa tenga errores.
3.  **Contexto bajo demanda**: Antes de tocar código, DEBO leer este archivo (`RULES_FOR_AI.md`).

### 🛠️ REGLAS DE EJECUCIÓN

- **NO EXPLORAR**: No uses `list_dir` o `grep_search` a menos que falte información crítica para el paso actual.
- **EARLY STOP**: Si una solución ya es funcional, detén el agente. No busques perfección "extra" que queme tokens.
- **LIMIT STEP**: Máximo 3-5 pasos por tarea.

### ⚙️ CONFIGURACIÓN DEL IDE (Manual)

- **Auto-Continue**: OFF
- **Agent Web Tools**: OFF (Solo ON si se pide específicamente)
- **Review Requirement**: Siempre pedir revisión antes de ejecuciones grandes.

---
