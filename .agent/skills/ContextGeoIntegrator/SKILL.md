# ContextGeoIntegrator

El "orquestador" que combina datos visuales con coordenadas geográficas.

## Instrucciones

Esta skill es responsable de la lógica de negocio final: decidir qué tipo de POI buscar basándose en lo que Vision detecta en la foto.

### Lógica Sugerida

- Si Vision detecta "food", buscar "restaurant|cafe".
- Si Vision detecta "nature", buscar "natural_feature|park".
- Si Vision detecta "monument", buscar "tourist_attraction".
