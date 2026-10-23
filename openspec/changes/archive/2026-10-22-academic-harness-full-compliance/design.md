# Technical Design: Cumplimiento Académico Total del Arnés y Optimización de Errores

## 1. Mapeo Universal de Errores Limpios en `llm_provider.py`

### Problema
Cuando una API como Groq u OpenAI responde con un código de error (ej. 429 cuota/tokens agotados, 401 clave inválida, 404 modelo no hallado), la librería OpenAI de Python levanta excepciones (`RateLimitError`, `AuthenticationError`, `NotFoundError`, `APIStatusError`) que contienen un volcado crudo de diccionarios JSON con metadatos internos, headers y traces. Esto confunde al usuario y deteriora la experiencia en la consola CLI.

### Solución Arquitectónica
- Se implementa una función `format_clean_api_error(error: Exception) -> str` en `harness/llm_provider.py`.
- Se inspecciona el código de estado HTTP (`error.status_code` si es `APIStatusError` o derivado):
  - **429**: `[Error 429 - Límite de Tokens/Cuota]: Se agotaron los tokens por minuto o la cuota del proveedor. Espere un momento o cambie de modelo con /model.`
  - **401**: `[Error 401 - Clave Inválida]: Clave de API no válida o revocada. Verifique su clave o use /model.`
  - **404**: `[Error 404 - Modelo no encontrado]: El modelo solicitado no existe o no tiene acceso en este proveedor.`
  - **400**: `[Error 400 - Solicitud Inválida]: Argumentos o sintaxis rechazada por el proveedor.`
  - **500 / 502 / 503**: `[Error 50x - Falla del Proveedor]: El servicio del modelo está temporalmente inaccesible.`
- En caso de errores generales de red o excepciones desconocidas, se extrae únicamente el mensaje legible sin estructuras JSON complejas.
- Se configura un parámetro de seguridad `max_tokens` (por defecto 1500) configurable para evitar desbordar los límites OTPM de tiers gratuitos.

## 2. Autorización por Lote `[s/n/a]` en `guardrails.py`

### Problema
Cuando el modelo realiza múltiples ediciones sucesivas sobre el mismo archivo en un turno (e.g. `write_file` seguido de varias ediciones o scripts), el usuario es obligado a confirmar `[s/n]` 5 o 6 veces para el mismo archivo.

### Solución Arquitectónica
- Se actualiza el prompt de confirmación interactiva en `harness/guardrails.py` a:
  `¿Desea autorizar esta operación? [s/n/a (autorizar todo para este archivo)]: `
- Opciones:
  - `s` / `si` / `y`: Autoriza la operación puntual actual.
  - `n` / `no`: Deniega la operación.
  - `a` / `all`: Autoriza la operación actual y registra la ruta del archivo en un conjunto temporal `_turn_approved_targets`.
- Si una operación posterior en el mismo turno opera sobre un objetivo previamente autorizado con `a`, se valida automáticamente sin re-preguntar al usuario.
- El conjunto de autorizaciones se limpia al inicio de cada nuevo turno del usuario en `main.py` o al completar el ciclo.

## 3. Gestión y Listado de Sesiones (`/sessions` y `/resume`)

### Contexto Académico
En las evaluaciones de clase, el profesor penalizó explícitamente a estudiantes que no contaban con listado y recuperación de sesiones previas.

### Solución Arquitectónica
- Se crea un subdirectorio `.harness_sessions/` en el espacio de trabajo activo (o en el directorio base).
- Cada sesión se guarda como un archivo JSON `.harness_sessions/<session_id>.json` que contiene:
  - `session_id`: identificador único (e.g. `session_20261022_223015`).
  - `created_at`: fecha y hora legible.
  - `provider` y `model`: configuración con la que se operó.
  - `messages`: lista ordenada de mensajes del historial.
- Comando `/sessions`:
  - Lee los archivos en `.harness_sessions/`.
  - Muestra una tabla ordenada cronológicamente con ID, fecha, modelo y conteo de mensajes.
- Comando `/resume <session_id>`:
  - Carga el archivo `.harness_sessions/<session_id>.json`.
  - Restaura el historial en memoria para continuar la conversación de forma transparente.

## 4. Compactación Inteligente de Contexto (`/compact`)

### Problema
Sesiones largas acumulan miles de tokens de contexto, provocando el error 429 (límite de tokens por minuto) en proveedores como Groq.

### Solución Arquitectónica
- Comando `/compact`:
  - Si el historial tiene más de 4 mensajes, extrae los mensajes intermedios.
  - Envía una petición concisa al modelo activo:
    `"Resume de forma ejecutiva y precisa los puntos clave del siguiente diálogo, acuerdos técnicos, archivos editados y estado actual, descartando charlas accesorias."`
  - Reemplaza el historial extenso por un mensaje consolidado del sistema:
    `[Contexto previo compactado: <resumen>]`
  - Reduce el contexto en un 70%-85%, liberando tokens inmediatamente.

## 5. Subagente Especializado con Contexto Aislado (Figura 1 del PDF)

### Especificación del PDF Académico
El PDF muestra en su Figura 1 que el orquestador principal delega una tarea a un subagente especializado con un contexto limpio. El subagente ejecuta sus pasos y retorna únicamente un resumen final al orquestador, evitando saturar la ventana de contexto del agente principal.

### Solución Arquitectónica
- Módulo `harness/subagent.py` (o función aislada en `agent_loop.py`):
  - Recibe: `task_description`, `cwd`, `provider`, `model`.
  - Instancia un ciclo acotado (`MAX_SUBAGENT_STEPS = 5`).
  - Contexto inicial limpio: únicamente las instrucciones de exploración y herramientas de solo lectura (`read_file`, `list_dir`, `search_code`).
  - Ejecuta la tarea de forma autónoma.
  - Retorna un string con el resumen ejecutivo de hallazgos.
- Herramienta `delegate_subagent(task: str)` disponible para el modelo principal.

## 6. Mínimo 3 Herramientas / Servidores MCP (Model Context Protocol)

### Requisito Académico
El trabajo exige la integración de un mínimo de 3 herramientas o integraciones bajo el protocolo MCP (Model Context Protocol).

### Solución Arquitectónica
Se implementa un conector y 3 herramientas MCP nativas en `harness/tools.py`:
1. `mcp_fetch`: Cliente de consulta HTTP/REST que recupera documentación técnica, endpoints o APIs externas con cabeceras limpias y truncado seguro.
2. `mcp_git_info`: Inspector MCP de repositorios Git (estado de ramas, último commit, diffs de cambios recientes sin salir del harness).
3. `mcp_sqlite_query`: Motor de consultas SQL de solo lectura sobre bases de datos locales SQLite para gestión de datos estructurados y memorias del proyecto.
- Todas integradas con JSON Schema riguroso y truncado estricto a 4000 caracteres.

## 7. Manual de Defensa Técnica (`DEFENSA_HARNESS.md`)

Para asegurar la máxima nota en la defensa oral individual del martes:
- Guía de arquitectura completa.
- Justificación de cada decisión técnica.
- Preguntas trampa del profesor y respuestas exactas con fundamento teórico y práctico.
