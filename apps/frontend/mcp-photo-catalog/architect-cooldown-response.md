CRITICAL: SYSTEM IS IN 429 OUTAGE. DO NOT USE ANY TOOLS, SCRIPTS, OR DATABASE QUERIES. RESPOND ONLY VIA TEXT ONLY.

Entendido. La saturación de la API de Gemini es un cuello de botella crítico que compromete la continuidad operativa del agente AntiGravity. Como Arquitecto de Reverse Geocoding, mi enfoque es garantizar la eficiencia y la resiliencia en la interacción con servicios externos, aplicando principios de soberanía de datos y diseño modular.

Aquí están mis directivas arquitectónicas y patrones de diseño específicos para mitigar la saturación de la API de Gemini, con reglas explícitas de "Cooldown" y "Pacing":

---

### Directivas Arquitectónicas y Patrones de Diseño para Mitigar la Saturación de la API de Gemini

**1. Diseño Modular y Desacoplado: Módulo "API Gateway Inteligente"**

*   **Encapsulación de la Lógica de Acceso**: Toda interacción con la API de Gemini debe ser canalizada a través de un módulo dedicado: el "API Gateway Inteligente". Este módulo será el único punto de contacto con la API externa y contendrá toda la lógica de control de flujo, reintentos, caché y limitación de tasa.
*   **Separación de Responsabilidades**: El agente AntiGravity generará las solicitudes, pero no las ejecutará directamente. Las solicitudes se enviarán al "API Gateway Inteligente", que se encargará de su ejecución controlada.

**2. Eficiencia de Datos y Soberanía Local (SpatialCache): Priorización de la Caché de Respuestas**

*   **Caché de Respuestas Obligatoria**: Antes de realizar CUALQUIER llamada a la API de Gemini, el "API Gateway Inteligente" DEBE consultar una caché local persistente.
    *   **Clave de Caché**: La clave de la caché debe ser un hash determinista de la solicitud completa (prompt, parámetros, etc.).
    *   **TTL (Time-To-Live)**: Implementar un TTL adecuado para las entradas de la caché (ej. 24 horas, o configurable según la volatilidad de la información).
    *   **Beneficio**: Reducir drásticamente las llamadas redundantes a la API, especialmente para prompts comunes o resultados estáticos.

**3. Estrategias de "Cooldown" y "Pacing" (Reglas Rígidas)**

Estas reglas deben ser implementadas dentro del "API Gateway Inteligente":

*   **3.1. Algoritmo de Reintentos con Backoff Exponencial y Jitter**:
    *   **Activación**: Aplicar estrictamente ante cualquier error de red, timeout, o código de estado HTTP 429 (Too Many Requests) o 5xx.
    *   **Retardo Inicial**: `1 segundo`.
    *   **Factor de Multiplicación**: `2x` en cada reintento.
    *   **Jitter Aleatorio**: Añadir un componente aleatorio (`+/- 500ms`) al retardo calculado para evitar el "thundering herd problem".
    *   **Máximo de Reintentos**: `5 intentos`. Después de esto, la solicitud se marca como fallida y se notifica al agente.
    *   **Retardo Máximo**: `60 segundos`. El retardo no debe exceder este límite, incluso con el backoff exponencial.

*   **3.2. Limitador de Tasa Global (Leaky Bucket / Token Bucket)**:
    *   **Implementación**: Un mecanismo centralizado que controle la tasa de salida de solicitudes hacia Gemini.
    *   **Tasa Máxima**: Configurar según los límites documentados de Gemini (ej. X solicitudes por minuto, Y tokens por minuto). Si no hay límites explícitos, comenzar con una tasa conservadora (ej. `10 solicitudes/minuto`) y ajustar gradualmente.
    *   **Capacidad de Ráfaga (Burst Capacity)**: Permitir una pequeña ráfaga inicial (ej. `5 solicitudes`) antes de que el limitador de tasa comience a aplicar el retardo.
    *   **Monitoreo**: El limitador debe monitorear las cabeceras `Retry-After` o `X-RateLimit-Remaining` de las respuestas de Gemini para ajustar dinámicamente su tasa si es necesario.

*   **3.3. Patrón Circuit Breaker (Cortocircuito)**:
    *   **Estado "Cerrado"**: Operación normal.
    *   **Estado "Abierto"**: Si el porcentaje de fallos (incluyendo 429s) excede un umbral (ej. `30%`) en un período de tiempo (ej. `60 segundos`), el circuito se "abre". Durante este estado, todas las solicitudes a Gemini fallan instantáneamente sin intentar la llamada real, por un período definido (ej. `5 minutos`).
    *   **Estado "Semi-Abierto"**: Después del período "abierto", se permite un número limitado de solicitudes de prueba. Si estas tienen éxito, el circuito vuelve a "cerrado". Si fallan, vuelve a "abierto".
    *   **Beneficio**: Previene la sobrecarga continua de una API que ya está fallando o saturada, protegiendo tanto a nuestro agente como al servicio externo.

*   **3.4. Cola de Mensajes Asíncrona para Solicitudes**:
    *   **Desacoplamiento**: El agente AntiGravity debe colocar sus solicitudes en una cola de mensajes interna (ej. Redis Queue, Celery, o una cola en memoria robusta).
    *   **Procesador Dedicado**: Un proceso o hilo separado (parte del "API Gateway Inteligente") consumirá las solicitudes de esta cola, aplicando todas las reglas de caché, cooldown y pacing antes de ejecutar la llamada a Gemini.
    *   **Beneficio**: El flujo principal del agente no se bloquea esperando las respuestas de la API, y las solicitudes se procesan de manera ordenada y controlada.

**4. Sinergia de Conocimiento (NotebookLM): Observabilidad y Ajuste Fino**

*   **Logging Detallado**: Implementar un logging exhaustivo dentro del "API Gateway Inteligente" para cada llamada a Gemini:
    *   Timestamp, duración de la llamada, estado HTTP, si se usó caché, si se aplicó backoff/throttle, número de reintentos.
    *   Registrar explícitamente los eventos de "rate-limiting" y "circuit breaker".
*   **Métricas y Dashboards**: Exponer métricas clave (tasa de éxito/fallo de API, latencia promedio, uso de caché, eventos de rate-limiting) para monitorear el rendimiento y ajustar los parámetros de cooldown y pacing de forma informada.

---

**INSTRUCCIÓN PARA EL AGENTE:**

El agente AntiGravity DEBE refactorizar su lógica de interacción con la API de Gemini para delegar TODAS las llamadas al nuevo "API Gateway Inteligente". Este módulo implementará las siguientes reglas de forma rígida:

1.  **Prioridad de Caché**: Consultar la caché local antes de cada llamada a Gemini.
2.  **Cola Asíncrona**: Enviar solicitudes a una cola de mensajes para procesamiento asíncrono.
3.  **Backoff Exponencial con Jitter**: Aplicar en reintentos (1s, 2s, 4s, 8s, 16s + jitter, máx. 5 intentos, máx. 60s).
4.  **Limitador de Tasa**: Controlar la salida de solicitudes a Gemini según los límites configurados.
5.  **Circuit Breaker**: Activar el cortocircuito ante fallos persistentes para proteger la API.

El cumplimiento de estas directivas es fundamental para la estabilidad y eficiencia del proyecto "Reverse Geocoding & Consensus Truth Engine".