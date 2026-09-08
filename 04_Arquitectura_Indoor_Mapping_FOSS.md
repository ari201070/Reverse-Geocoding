# 04. Arquitectura: Reemplazo FOSS y Zero-OPEX para Visio AI (Planos de Interior y Mapas de Distribución)

**Propósito:** Este documento formaliza la integración de soluciones FOSS para la visualización, renderizado y modelado inteligente de mapas de interiores (floor plans/blueprints) y layouts arquitectónicos dentro del proyecto "Reverse Geocoding & Consensus Truth Engine". Su objetivo es extender la inferencia de la "Verdad del Lugar" a entornos interiores, soportar la determinación de azimut en espacios cerrados y mantener la estrategia de Zero-OPEX.

## 🏢 Reemplazo FOSS para Visio AI

### 1. Diagramación y Diseño de Distribución: diagrams.net (Draw.io)
- **Descripción:** Herramienta de diagramación completamente FOSS, gratuita y enfocada en la privacidad.
- **Uso en el Proyecto:** Admite el diseño de planos de planta interactivos, modelado de servidores y redes, diagramas de flujo y layouts organizacionales. Puede integrarse fácilmente como editor visual dentro de aplicaciones web para la creación o modificación de esquemas internos.

### 2. Modelado de Interiores en 3D: Sweet Home 3D
- **Descripción:** Aplicación de diseño de interiores de código abierto.
- **Uso en el Proyecto:** Permite dibujar planos de casa en 2D, colocar muebles y visualizar los resultados en una interfaz 3D en tiempo real. Es crucial para importar planos existentes (ej. imágenes aéreas o blueprints) para calcarlos y convertirlos en modelos espaciales estructurados, proporcionando una base para la granularidad de la "Verdad del Lugar" a nivel de objeto o habitación.

### 3. Visualización y Edición de Interiores en OpenStreetMap:
Si los mapas de interiores se integran en un contexto GIS/mapas interactivos:
- **OpenLevelUp! (`https://openlevelup.net/`)**:
    - **Descripción:** Visualizador open-source web diseñado específicamente para mostrar mapas de interiores multinivel (por pisos) utilizando los datos estructurados de OpenStreetMap (`indoor=room`, `level=1`, etc.).
    - **Uso en el Proyecto:** Permite la visualización interactiva de la "Verdad del Lugar" en entornos interiores, facilitando la comprensión espacial y la navegación.
- **OsmInEdit**:
    - **Descripción:** Editor web de código abierto diseñado para crear y editar fácilmente planos de plantas directamente sobre la base de datos de OpenStreetMap.
    - **Uso en el Proyecto:** Proporciona una interfaz para la contribución y mantenimiento de datos de mapas interiores, asegurando que la información espacial sea precisa y esté actualizada, y que se integre con la estrategia de datos abiertos.
