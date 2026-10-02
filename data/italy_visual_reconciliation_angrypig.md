# Informe de Reconciliación Visual - Angry Pig Restaurant (Roma)

## 🏛️ Caso de Prueba: Ventana 18:22:35 a 18:31:29 (03-Octubre-2023)

### 1. Diagnóstico y Resolución del Hito "Angry Pig"
- **Análisis Visual:** La ráfaga (18:22:35–18:31:29) corresponde a una escena de interior y exterior en un restaurante con identidad gráfica "Angry Pig", porchetta, y menciones a Colorado.
- **Técnica:** Se aplicó la **técnica de ventanas deterministas** utilizada en el caso Fontana di Trevi: se identificó la ráfaga, se descartó el origen erróneo del voucher (Vaticano) y se ha reasignado al nuevo punto de interés identificado por el usuario ("Angry Pig restaurant").
- **Coordenadas:** En ausencia de una entrada específica en `data/landmarks/*.geojson` para este local, se han mantenido temporalmente las coordenadas del área circundante (`41.9060, 12.4828`) para asegurar la coherencia cinemática dentro del bloque, marcando el origen de datos como `VISUAL_LANDMARK_STRICT`.

---

### 2. Registro de Fotos Auditadas y Corregidas

| Archivo | Hora | Corrección Física / BD |
| :--- | :--- | :--- |
| `2023-10-03 18.22.35_IMG_20231003_182235.jpg` | 18:22:35 | Angry Pig restaurant, Roma, Italia |
| `2023-10-03 18.23.52.jpg` | 18:23:52 | Angry Pig restaurant, Roma, Italia |
| `2023-10-03 18.24.39.jpg` | 18:24:39 | Angry Pig restaurant, Roma, Italia |
| `2023-10-03 18.24.48.jpg` | 18:24:48 | Angry Pig restaurant, Roma, Italia |
| `2023-10-03 18.25.07.jpg` | 18:25:07 | Angry Pig restaurant, Roma, Italia |
| `2023-10-03 18.25.29.jpg` | 18:25:29 | Angry Pig restaurant, Roma, Italia |
| `2023-10-03 18.31.23_IMG_20231003_183123.jpg` | 18:31:23 | Angry Pig restaurant, Roma, Italia |
| `2023-10-03 18.31.29_IMG_20231003_183129.jpg` | 18:31:29 | Angry Pig restaurant, Roma, Italia |

---

### 3. Explicación de la Técnica de Resolución
1. **Identificación de Ventana:** Se utiliza la secuencia cronológica de archivos (`18:xx`) para crear una **ventana de ráfaga ininterrumpida**.
2. **Rechazo de Heurística de Voucher Genérico:** Al detectar que el voucher del Vaticano (el que estaba "en curso" según el sistema) estaba contaminando erróneamente esta ventana, se aplica un **corte de asociación documental**, permitiendo que la información visual (el hito) prevalezca.
3. **Persistencia Atómica:** La corrección se realiza simultáneamente en la `photo_catalog.db` (actualización de 8 filas) y en el metadato EXIF físico (`ImageDescription`, `UserComment` con H3, `GPS`), garantizando que la fuente de verdad esté alineada en ambos niveles.
4. **Validación:** Se confirma visualmente que el hito no es el que el sistema intentaba asignar. Si el lugar no existe en el índice de landmark, se crea la entrada `VISUAL_LANDMARK_STRICT` como marcador de posición para futuras integraciones.
