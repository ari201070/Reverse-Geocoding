Entendido. Como Arquitecto de Reverse Geocoding, abordaremos la definición de la estructura de viajes/actividades con un enfoque modular y priorizando la fuente de verdad más fiable. La clave será la sinergia entre los metadatos de las fotos, la información de los documentos de viaje y la geolocalización espacial.

### Estrategia de Arquitectura para la Estructura de Viajes/Actividades

Proponemos un motor de clasificación de viajes/actividades basado en los siguientes módulos, priorizando la eficiencia de datos y la soberanía local.

#### Módulo 1: Ingesta y Normalización de Datos Crudos

1.  **Metadatos de Fotos:**
    *   Extraer `DateTimeOriginal` (fecha de toma), `DateTimeDigitized`, `GPSLatitude`, `GPSLongitude`, `FileName`.
    *   **Problema 2 (Fechas de subida/actualización):** `DateTimeOriginal` será la fuente primaria para la fecha de la foto. Si no existe, se intentará `DateTimeDigitized`. Las fechas de modificación/creación del archivo serán un último recurso y se marcarán como "potencialmente no fiables". Las fechas futuras (ej. Argentina 2026) se identificarán y se priorizará la fecha del documento de viaje para el rango del viaje.
2.  **Documentos de Viaje (F:\Documentos_Viaje\, G:\האחסון שלי\):**
    *   Implementar un parser (manual o semi-automático) para extraer:
        *   **Fechas de inicio y fin del viaje:** Esta es la **fuente de verdad principal** para la duración de un viaje.
        *   **Países y Ciudades clave:** Nombres de hoteles, aeropuertos, destinos principales.
        *   **Tipo de documento:** Reserva de hotel, billete de vuelo, itinerario.
    *   Asociar cada documento a un identificador de viaje provisional.

#### Módulo 2: Resolución de Verdad Temporal y Espacial (SpatialCache & H3)

1.  **Resolución de Fechas del Viaje:**
    *   Para cada viaje identificado por documentos, establecer un rango de fechas `[Trip_StartDate, Trip_EndDate]` basado en la información más precisa de los documentos. Si hay múltiples documentos, se tomará el rango que abarque todas las actividades confirmadas.
2.  **Geocodificación y H3 Clustering:**
    *   Para cada foto con GPS:
        *   Convertir `GPSLatitude`/`GPSLongitude` a un índice H3 (resolución 8-10 para granularidad de ciudad/región).
        *   Realizar Reverse Geocoding (priorizando SpatialCache local) para obtener País, Región/Estado, Ciudad.
    *   Para ubicaciones extraídas de documentos (ciudades, hoteles):
        *   Geocodificar estas ubicaciones a `Lat/Lon` y H3.
    *   **Problema 1 (Grecia vs. Creta):** El Reverse Geocoding debe ser lo suficientemente granular para distinguir islas o regiones autónomas significativas. Si todas las fotos y documentos apuntan a "Creta" dentro de "Grecia", el viaje se categorizará como "Creta".
    *   **Problema 4 (Italia 2023 - Firenze/Pisa):** El clustering H3 de las fotos dentro del rango de fechas del viaje permitirá identificar los focos de actividad. Si el 100% de las fotos de un viaje "Italia" se concentran en Firenze y Pisa durante 2 días, el viaje se refinará a "Italia (Firenze, Pisa)".

#### Módulo 3: Motor de Clasificación de Viajes y Actividades

Este es el núcleo del "Reverse Geocoding & Consensus Truth Engine".

1.  **Definición de "TravelBooking" (Tipo de Viaje):**
    *   Se creará una entidad `TravelBooking` con los siguientes atributos:
        *   `ID_Viaje` (UUID)
        *   `Nombre_Viaje` (ej. "Argentina 2011-2012", "Eslovenia 2015", "Creta 2013")
        *   `Tipo_Viaje` (ENUM: `Internacional`, `Local`, `Actividad_Especial`)
        *   `Fecha_Inicio_Real` (de documentos)
        *   `Fecha_Fin_Real` (de documentos)
        *   `Pais_Principal` (ej. "Argentina", "Eslovenia", "Grecia" -> "Creta")
        *   `Paises_Visitados` (Lista: ej. ["Croacia", "Montenegro"])
        *   `Ciudades_Visitadas` (Lista: ej. ["Dubrovnik", "Kotor"])
        *   `H3_Clusters_Principales` (Lista de H3s representativos del viaje)
        *   `Documentos_Asociados` (Lista de rutas a los documentos)
        *   `Notas` (ej. "Fechas de fotos 2026 son de subida, no de toma")
        *   `Estado` (ENUM: `Confirmado`, `Planificado`, `Localizado`)

2.  **Proceso de Asignación y Creación:**

    *   **Paso A: Creación de Viajes Internacionales (Documento-Primero):**
        *   Iterar sobre los documentos de viaje. Cada conjunto de documentos coherente (mismo país, fechas solapadas) define un `TravelBooking` de tipo `Internacional`.
        *   **Problema 5 (Bosnia 2023):** Aunque solo haya 1 foto geolocalizada, la existencia del documento `BIH 2304 טבלת מלונות וטיסות עבור אריאל פליאר.pdf` es suficiente para crear el `TravelBooking` "Bosnia 2023" con sus fechas y país. La foto se asignará a este viaje.
        *   **Problema 1 (Grecia/Creta):** Si el Reverse Geocoding de las 9 fotos y/o la información de los documentos confirma que todas las ubicaciones están en Creta, el `Pais_Principal` será "Creta" y el `Nombre_Viaje` "Creta 2013".

    *   **Paso B: Asignación de Fotos a Viajes Internacionales:**
        *   Para cada foto con `DateTimeOriginal` y GPS:
            *   Intentar asignarla a un `TravelBooking` existente si su `DateTimeOriginal` cae dentro de `[Trip_StartDate, Trip_EndDate]` Y su `Pais` geolocalizado coincide con `Pais_Principal` o `Paises_Visitados` del viaje.
            *   **Problema 2 (Fechas incorrectas):** Si `DateTimeOriginal` está fuera del rango del viaje pero la geolocalización es consistente, se marcará la foto y se priorizará el rango del viaje para su asignación. Se podría añadir una nota a la foto o al viaje.

    *   **Paso C: Identificación y Creación de "Visitas Locales/Actividades":**
        *   **Problema 3 (Visitas locales de Israel):** Todas las fotos no asignadas a un `TravelBooking` de tipo `Internacional` y cuyo `Pais` geolocalizado sea "Israel" serán candidatas para `Tipo_Viaje = Local` o `Actividad_Especial`.
        *   Agrupar estas fotos localmente:
            *   Clustering temporal: Fotos tomadas en un rango corto (ej. 1-3 días).
            *   Clustering espacial: Fotos dentro de un radio H3 cercano.
            *   Ejemplos: "Israel 2008: Negev Desert Trip", "Israel 2010: Nachal Dror Hike".
            *   Las "screenshots" de Israel 2025 se identificarán por su tipo de archivo/metadatos y se podrán agrupar como "Actividad_Especial: Capturas Tel Aviv".

    *   **Paso D: Refinamiento de Granularidad (Ej. Italia 2023):**
        *   Para viajes donde los documentos indican un país amplio (ej. "Italia") pero las fotos se concentran en una región específica y corta (Firenze y Pisa, 2 días):
            *   El `TravelBooking` inicial será "Italia 2023".
            *   Los `Ciudades_Visitadas` se actualizarán a ["Firenze", "Pisa"] basándose en el Reverse Geocoding de las fotos.
            *   Se podría añadir una nota o incluso crear un `Sub_Actividad` si la complejidad lo justifica, pero para este caso, refinar `Ciudades_Visitadas` es suficiente.

#### Módulo 4: Salida y Persistencia

1.  **Estructura de Salida:** Generar un conjunto de objetos `TravelBooking` y una tabla de asignación `Foto_ID -> ID_Viaje`.
2.  **Persistencia:** Almacenar esta estructura en la base de datos `photo_catalog.db` o una base de datos dedicada a viajes.

---

### Resumen de Solución a Problemas Identificados:

1.  **"Greece" cuando debería ser "Crete":** El Módulo 2 (Reverse Geocoding y H3) y Módulo 3 (Clasificación) se encargarán de identificar "Creta" como `Pais_Principal` o `Region_Principal` si la evidencia espacial y documental lo soporta.
2.  **Fechas de subida/actualización:** El Módulo 1 prioriza `DateTimeOriginal`. El Módulo 2 utiliza las fechas de los documentos como la fuente de verdad para el rango del viaje, permitiendo identificar y anotar fotos con fechas inconsistentes.
3.  **Visitas locales de Israel:** El Módulo 3 distingue claramente entre `Tipo_Viaje = Internacional` (documento-driven) y `Tipo_Viaje = Local` (geolocalización y clustering temporal en el país de origen).
4.  **Italia 2023 (Firenze+Pisa):** El Módulo 3 refinará los `Ciudades_Visitadas` del `TravelBooking` "Italia 2023" basándose en el clustering H3 de las fotos, reflejando la realidad del viaje corto.
5.  **Bosnia 2023 (1 foto, pero documentos):** El Módulo 3 creará el `TravelBooking` "Bosnia 2023" basándose en el documento, incluso con una foto mínima, validando la existencia del viaje por la fuente documental.

Esta estructura modular asegura que cada componente sea testeable y que la lógica de decisión sea clara y jerárquica, optimizando el uso de datos locales antes de recurrir a servicios externos.

---

INSTRUCCIÓN PARA EL AGENTE:
Implementar los módulos descritos:
1.  **Módulo 1: Ingesta y Normalización de Datos Crudos.**
2.  **Módulo 2: Resolución de Verdad Temporal y Espacial (SpatialCache & H3).**
3.  **Módulo 3: Motor de Clasificación de Viajes y Actividades.**
4.  **Módulo 4: Salida y Persistencia.**

Priorizar la extracción de fechas y ubicaciones de los documentos de viaje como la fuente de verdad para la creación de `TravelBooking` de tipo `Internacional`. Utilizar `DateTimeOriginal` de las fotos y el clustering H3 para asignar fotos y refinar la granularidad de los viajes. Distinguir explícitamente entre `Internacional` y `Local` para los `Tipo_Viaje`.