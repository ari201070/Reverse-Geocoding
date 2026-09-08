# SKILL-physiognomy: Habilidad Genérica de Fisonomía Comercial y Coherencia de Marcas

## Objetivo
Validar y elevar de forma proactiva la confianza de la geocodificación mediante la correlación abstracta de firmas visuales/fisonómicas de establecimientos comerciales con los nombres de marca o tipos de negocio detectados en el texto OCR. Esto permite resolver ambigüedades espaciales y direcciones postales genéricas en cualquier parte del mundo sin depender de APIs propietarias de geocodificación en la nube.

## Principios de Diseño Global y Abstracto
Este motor está diseñado bajo un paradigma estrictamente agnóstico a la región, marca o idioma específico. Se basa en una jerarquía tipológica que mapea características de diseño arquitectónico y de interiores (fisonomía) a categorías de negocio de alcance universal.

---

## Firmas Fisonómicas y Claves Visuales de Diseño

El sistema clasifica las observaciones visuales en cuatro grandes firmas de diseño comercial que se asocian con categorías genéricas de negocio:

### 1. Boutique de Alimentos y Chocolaterías / Confiterías
*   **Marcadores Fisonómicos Directos:** 
    *   Vitrinas de exhibición horizontales de cristal templado, con iluminación cálida focalizada en los productos.
    *   Estantes de madera noble o metal pulido exhibiendo cajas individuales alineadas geométricamente.
    *   Colores de acento premium (bronce, dorado, negro mate, maderas oscuras).
    *   Mostradores de mármol o cuarzo.
*   **Asociación OCR Esperada:** Marcas de chocolates finos, pastelerías artesanales, reposterías, confiterías, salones de té o palabras clave relacionadas ("artesanal", "chocolate", "delicatessen").

### 2. Cafeterías de Especialidad y Salones de Café
*   **Marcadores Fisonómicos Directos:**
    *   Máquinas de espresso industriales visibles (de palanca o múltiples grupos) en barras de servicio de acero inoxidable, madera o azulejo rústico.
    *   Bolsas de granos de café de arpillera o papel kraft apiladas o en estanterías.
    *   Molinos de café, jarras de arte latte, filtros cónicos (V60, Chemex).
    *   Mesas de madera pequeña o barras altas con taburetes.
*   **Asociación OCR Esperada:** Marcas de café internacionales o locales, tostadores, salones de café, o palabras clave ("espresso", "brew", "roasters", "café", "coffehouse").

### 3. Restaurantes y Establecimientos de Comida Rápida / Casual
*   **Marcadores Fisonómicos Directos:**
    *   Menús retroiluminados sobre el mostrador de pedidos, terminales de punto de venta (POS) orientadas al cliente.
    *   Disposición repetitiva de mesas de melamina o plástico, sillas de metal o cabinas (booths) tapizadas en vinilo.
    *   Cocina abierta o semicerrada con campanas de extracción de acero inoxidable visibles.
    *   Señalética de recogida de pedidos (pick-up / entrega).
*   **Asociación OCR Esperada:** Cadenas de hamburgueserías, pizzerías, comida rápida o palabras clave ("burgers", "pizza", "grill", "fast-food", "comida").

### 4. Tiendas de Moda / Flagship Stores / Boutiques de Ropa
*   **Marcadores Fisonómicos Directos:**
    *   Maniquíes vestidos con prendas de temporada situados en la entrada o detrás de ventanales (escaparates).
    *   Racks lineales de metal o percheros colgantes con ropa organizada por colores o tipos.
    *   Probadores con cortinas gruesas o puertas con espejos de cuerpo entero.
    *   Iluminación de riel (track-lighting) orientada direccionalmente.
*   **Asociación OCR Esperada:** Marcas de ropa, calzado, moda rápida o palabras clave ("fashion", "store", "boutique", "outfit", "design").

### 5. Bodegones Tradicionales, Restaurantes de Campo y Paradores del Delta / Río
*   **Marcadores Fisonómicos Directos:**
    *   Vajilla de estilo vintage/retro: jarros de metal enlozado (esmaltados en amarillo, verde, blanco con bordes oscuros), vasos de vidrio grueso (tipo boliche o "vaso de vino de mesa"), cubiertos rústicos o platos/bandejas individuales de hierro fundido o chapa.
    *   Mobiliario e individuales: mesas de madera maciza o tablas de presentación rústicas sobre las cuales se sirven alimentos de confitería o parrilla (croissants/medialunas, picadas, empanadas, asado). Individuales de papel rústico, rosa o blanco, con tramas impresas de redes sociales o códigos QR de mesa.
    *   Ambiente y acabados: paredes de ladrillo visto, revestimientos de madera tratada para intemperie, techos de chapa canalizada o vigas de madera expuestas; vistas directas a muelles, agua o vegetación selvática a través de ventanas.
*   **Asociación OCR Esperada:** Nombres de bodegones, parrillas tradicionales, paradores de río, nombres de islas o palabras clave relacionadas ("asador", "bodegón", "parador", "delta", "isla", "embarcadero", "almacén", "recreo").

---

## Regla de Ponderación de Confianza (Fisonomía + OCR)

El núcleo del motor de consenso utiliza una regla determinista para elevar la confianza cuando coinciden la fisonomía y el texto OCR:

$$\text{Si } ( \text{FisonomíaDetectada} \in \text{Categoría} ) \land ( \text{OCR\_Detectado} \in \text{Categoría} ) \implies \text{Confianza} = 0.90 \text{ (Estado: RECONSTRUCTED)}$$

### Algoritmo de Decisión de Confianza
1. **Detección Visual:** El modelo visual (Moondream o similar) detecta la presencia de marcadores físicos fuertes (ej. "vitrinas horizontales de chocolates" o "máquina de espresso industrial").
2. **Detección OCR:** La API de visión detecta un fragmento de marca o nombre en el letrero (ej. "Rapanui", "Starbucks", "Boutique de Cafe", "Saks").
3. **Mapeo de Categoría:** El sistema mapea tanto la firma visual como el OCR a una categoría global común (ej. "Boutique de Alimentos y Chocolaterías" o "Cafetería").
4. **Verificación de Coherencia:** Si la intersección es positiva, se emite un veredicto de validación cruzada fisonómica. El nivel de confianza del puzzle se reescribe proactivamente a `0.90` (clasificado como `RECONSTRUCTED`). Esto permite dar por válida la ubicación geocodificada de la marca (obtenida de la base de datos o el SpatialCache), ignorando la imprecisión del GPS crudo o de direcciones postales genéricas.

---

## IV. Protocolo de Extracción y Decodificación de Códigos QR por Visión Multimodal (Gemini / "Gem")

Cuando una imagen contiene un código QR visible en el entorno físico directo de la foto (carteles acrílicos de mesa, individuales impresos de papel, letreros de pared, menús en mostradores):

1.  **Detección Multimodal Activa (Visual QR Parsing):** El agente desarrollador de IA ("Gem") no debe tratar el código QR como un mero elemento decorativo o un vector gráfico pasivo. Debe utilizar la capacidad de procesamiento de píxeles nativa del modelo multimodal para escanear y decodificar el código QR directamente, aislando la URL o cadena codificada.
2.  **Identificación de "Anchor Slugs" en URLs:** Al decodificar el QR, se extraen enlaces web de cartas o menús digitales (ej. `https://menu.digital/la-isla` o `https://laislares.com/menu`). El "slug" de la marca o local (ej: `la-isla`) actúa como una **Huella Digital Semántica** e identificador unívoco.
3.  **Fusión Espacial contra el Rebote de Señal (GPS Desviado):**
    *   En zonas costeras, montañosas o del Delta (frecuentemente afectadas por interferencias y rebotes de señal GPS de hasta 1 km), el GPS crudo suele colocar la foto en la orilla opuesta o en centros urbanos masivos adyacentes (ej: situar "La Isla Restaurante" en el "Puerto de Frutos", a 480 metros de distancia).
    *   Si el desvío geográfico entre las coordenadas estimadas del GPS crudo ($L_{gps}$) y la coordenada real indexada de la marca decodificada del QR ($L_{com}$) es menor a **1.5 km** (dentro del área de influencia de la misma celda H3 resolución 7 u 8), **la ubicación de la marca tiene prioridad absoluta**.
4.  **Veto Positivo y Corrección de Coordenadas:**
    El sistema descarta automáticamente la coordenada imprecisa del GPS crudo y reescribe la ubicación de la foto a las coordenadas rooftop exactas del comercio ($L_{com}$), asignándole un nivel de confianza final de **`0.95` (Estado: RECONSTRUCTED)** por validación dura, sin requerir intervención humana.

---

## Guardrails de Soberanía y Operación Offline
- **Independencia de APIs de Nube:** La verificación de la fisonomía de marca debe basarse en modelos visuales locales o en el motor de consenso offline para garantizar que las fotos privadas de fachadas e interiores no se transmitan a servicios de terceros.
- **Soberanía del Dato:** El cruce se realiza localmente utilizando el diccionario de marcas asociadas a la celda H3, respetando la privacidad del usuario al no indexar identidades individuales, sino firmas comerciales genéricas.

