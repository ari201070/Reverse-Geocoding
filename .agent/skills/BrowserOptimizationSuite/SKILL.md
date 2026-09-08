# Skill: BrowserOptimizationSuite

Skill especializada en la optimización del entorno de desarrollo y compatibilidad entre navegadores.

## 🌐 Políticas de Navegador

- **Navegador Preferido**: Google Chrome.
  - Siempre que se proporcione una URL de `localhost`, se recomienda al usuario abrirla en Chrome para máxima compatibilidad con las APIs de Google Maps y Picarta.
  - El agente debe intentar usar comandos que especifiquen Chrome si el sistema lo permite (ej: `start chrome http://localhost:3000`).

## 🛠️ Troubleshooting de Compatibilidad

### Microsoft Edge

- **Tracking Prevention**: Si Edge bloquea el acceso a `storage`, se debe instruir al usuario a:
  1. Ir a `edge://settings/privacy`.
  2. En "Tracking prevention", agregar `localhost` a las excepciones o cambiar a modo "Balanced".

### Google Chrome

- **PWA/Service Workers**: Chrome es el entorno de referencia para la depuración de Service Workers en este proyecto.

## 🚀 Comandos de Inicio Optimizado

- **Windows**: `start chrome http://localhost:3000`
- **Mac**: `open -a "Google Chrome" http://localhost:3000`
- **Linux**: `google-chrome http://localhost:3000`
