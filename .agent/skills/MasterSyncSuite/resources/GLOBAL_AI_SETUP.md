# GUÍA DE CONFIGURACIÓN GLOBAL (IDE/PLATAFORMA)

Para que Antigravity o cualquier agente siga estas reglas sin que tengas que pedírselo cada vez, busca estas secciones según tu herramienta:

## 1. Si usas CURSOR

- **Global**: `Settings` (Cmd/Ctrl + Shift + J) -> `General` -> `Rules for AI`. Pega aquí el contenido de `RULES_FOR_AI.md`.
- **Por Proyecto**: Crea un archivo `.cursorrules` en el root (es lo mismo que `RULES_FOR_AI.md`).

## 2. Si usas VS CODE (Gemini / Copilot)

- **Copilot**: Haz clic en el icono de Copilot -> `...` (More Actions) -> `Settings` -> `Custom Instructions`.
- **Gemini Code Assist**: Busca `System Instructions` en la configuración de la extensión.

## 3. Si usas la interfaz Web (Gemini / ChatGPT)

- Ve a tu Perfil -> `Personalizar Gemini` o `Instrucciones personalizadas`. Pega el bloque allí.

## 4. Ajustes Específicos (Agent Settings)

Busca estos interruptores en la configuración de la extensión/plugin del agente:

- **Auto-Continue**: Busca "Allow agent to automatically continue". Cámbialo a **OFF**.
- **Web Tools**: Busca "Enable Search" o "Web Access". Cámbialo a **OFF**.
- **Steps Limit**: No siempre es editable, pero si ves un "Max iterations per task", bájalo a **5**.

---

> [!TIP]
> Si no encuentras la opción exacta, dime el nombre de la extensión o plataforma específica que estás usando y podré darte pasos exactos.
