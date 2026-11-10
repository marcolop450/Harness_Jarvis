# Design: Arquitectura del Arnés Jarvis a Grado de Producción

## Context
Ver `proposal.md` para la motivación y el alcance general. El sistema actual opera como un CLI interactivo en terminal implementado en Python puro sobre 6 módulos en `harness/` (`main.py`, `model_config.py`, `llm_provider.py`, `agent_loop.py`, `guardrails.py`, `tools.py`, `mcp_client.py`). Las limitaciones actuales incluyen redundancia de runtime (servidor filesystem de Node.js en `package.json`), corte ciego de salidas a 4000 caracteres perdiendo trazas de error, fatiga de confirmación interactiva `[s/n]`, fragilidad ante errores de cuota HTTP 429 y JSONs imperfectos emitidos por modelos locales/pequeños, y saturación prematura de la ventana de contexto sin inyección estructurada del entorno.

Este diseño define cómo evolucionar cada módulo de forma atómica y robusta bajo la analogía del "Sistema Operativo y Automóvil de Carreras", preservando cero dependencias de frameworks pesados (cero LangChain/CrewAI).

## Goals / Non-Goals

**Goals:**
- **Runtime 100% Python y MCP Resiliente:** Eliminar Node.js del entorno, dejando las operaciones de disco a `tools.py` y otorgando degradación elegante (*graceful degradation*) a los servidores MCP stdio (`fetch`, `git`).
- **Gobernanza Smart HITL en 3 Niveles:** Nivel 0 (Auto-aprobado para lectura), Nivel 1 (Escritura en workspace con memoria de sesión persistente `[a]`), Nivel 2 (Comandos con whitelist segura y confirmación estricta libre de command injection).
- **Resiliencia de Inferencia Multi-API:** Aumentar `max_tokens` a 4096, reintentos con Exponential Backoff ante HTTP 429 e indicador en consola, y extractor/reparador de JSON para `tool_calls` que auto-sana errores de sintaxis y devuelve errores de esquema al bucle de agente.
- **Truncado Inteligente Head+Tail:** Preservar 1000 caracteres iniciales y 3000 finales con marcador explícito de caracteres omitidos.
- **Inteligencia de Contexto y Kernel:** Inyección proactiva de contexto ambiental en el System Prompt (SO, cwd, árbol resumido, estado Git y `JARVIS.md`), Observation Masking sobre copia efímera para pasos antiguos (>5 pasos) preservando integridad de `tool_call_id`, y bucle de auto-reparación (Self-Healing).

**Non-Goals:**
- No se incorporan frameworks externos como LangChain, LlamaIndex o CrewAI.
- No se migra a interfaces gráficas web; el CLI terminal REPL sigue siendo la interfaz canónica.
- No se reemplaza el almacenamiento de sesiones en JSON por bases de datos cliente-servidor externas.

## Decisions

### 1. Eliminación de Runtime Node.js MCP y Degradación Elegante en stdio
- **Decisión:** Descartar `@modelcontextprotocol/server-filesystem`, eliminar `package.json` y `package-lock.json`, y mantener únicamente `mcp-server-fetch` y `mcp-server-git` en `mcp.json`. En `harness/mcp_client.py`, envolver la inicialización de cada servidor MCP en un bloque `try/except` que capture fallos de conexión o binarios ausentes, emita un `logger.warning` sin bloquear y permita al CLI iniciar con normalidad.
- **Alternativas consideradas:**
  - *Mantener el servidor filesystem en Node.js:* Rechazado por duplicidad innecesaria con `tools.py` y fragilidad de dependencias npm en Windows.
  - *Instalar un servidor filesystem alternativo en Python:* Rechazado porque `tools.py` ya implementa validaciones de guardrails nativas (`guardrails.py`) que un MCP externo no garantiza sin overhead.

### 2. Gobernanza de Seguridad Smart HITL en 3 Niveles y Memoria de Sesión `[a]`
- **Decisión:** Unificar la validación en `harness/guardrails.py` mediante la función `authorize_and_dispatch(tool_name, args, session_approved_targets)`:
  - *Nivel 0 (Lectura/Auto):* `read_file`, `list_dir`, `search_code`, consultas `SELECT` en `sqlite_query`, y comandos Git de solo lectura (`status`, `diff`, `log`). Se ejecutan sin confirmación.
  - *Nivel 1 (Escritura en Workspace con Memoria `[a]`):* `write_file`, `edit_file` y mutaciones en base de datos. Si el usuario selecciona `a` (*all*), el identificador o ruta normalizada se registra en `session_approved_targets: set[str]`, suprimiendo confirmaciones futuras para ese archivo durante la sesión activa.
  - *Nivel 2 (Comandos y Red):* `run_command` y llamadas MCP de red (`fetch`). Los comandos se verifican contra una lista blanca segura (`pytest`, `python -m unittest`, `git status`, `git diff`, `git log`, `ruff`, `black --check`, `mypy`). Se prohíbe taxativamente la presencia de operadores de encadenamiento o redirección shell (`;`, `&&`, `||`, `|`, `` ` ``, `$()`, `>`, `<`, saltos de línea `\n`). Si contiene encadenamiento o no está en la lista blanca, exige confirmación interactiva `[s/n/a]`.
- **Alternativas consideradas:**
  - *Modo `-y` global:* Rechazado por riesgo inaceptable de borrado de archivos o ejecuciones no deseadas.
  - *Confirmación por turno único:* Rechazado por provocar fatiga severa en flujos iterativos de edición de código.

### 3. Resiliencia Multi-API: Exponential Backoff ante 429 y `max_tokens=4096`
- **Decisión:** En `harness/llm_provider.py`:
  - Incrementar `max_tokens` de 1500 a 4096.
  - Implementar `call_llm_with_backoff(model_config, messages, tools=None, max_retries=5)`: Si la llamada genera una excepción HTTP 429 o `RateLimitError`, inspeccionar la cabecera `Retry-After` (si está presente). En su defecto, calcular `delay = (base_delay * 2^attempt) + jitter` (con `base_delay = 2.0s`), imprimir un mensaje claro en consola indicando el tiempo de espera y reintentar hasta `max_retries`.
- **Alternativas consideradas:**
  - *Fallo inmediato con advertencia:* Rechazado porque detiene tareas largas y autónomas por picos transitorios de cuota.
  - *Espera fija sin jitter:* Rechazado porque satura los endpoints si hay múltiples llamadas concurrentes o sincronizadas.

### 4. Reparador de JSON y Bucle de Auto-reparación (Self-Healing)
- **Decisión:** En `harness/llm_provider.py` y `harness/agent_loop.py`:
  - Los modelos pequeños o locales (Ollama, LM Studio, Groq) a menudo envuelven argumentos de `tool_calls` en bloques de código markdown (` ```json ... ``` `) o introducen comas colgantes y comillas sin escapar. Crear una función `repair_json_arguments(raw_json: str) -> dict` que limpie bloques markdown, corrija comas finales y parsee el JSON.
  - Si el JSON no puede ser recuperado, **no abortar la ejecución**. Retornar al modelo un mensaje con `role: "tool"` conteniendo el error de parsing exacto para que el LLM reescriba su llamada en el siguiente paso del bucle.
- **Alternativas consideradas:**
  - *Lanzar excepción y salir del REPL:* Rechazado por romper la autonomía del arnés.
  - *Ignorar la llamada de herramienta defectuosa:* Rechazado porque deja al LLM en un bucle ciego sin saber por qué falló su comando.

### 5. Truncado Inteligente Head+Tail (`smart_truncate` 1000 + 3000)
- **Decisión:** En `harness/tools.py`:
  - Reemplazar el truncado simple por `smart_truncate(text: str, head_chars: int = 1000, tail_chars: int = 3000, max_chars: int = 4000) -> str`. Si `len(text) > max_chars`, conservar los primeros 1000 caracteres, insertar `\n\n[... {omitted_count} caracteres omitidos por el arnés para proteger la ventana de contexto ...]\n\n`, y los últimos 3000 caracteres (donde residen los stack traces y resúmenes de error).
  - Añadir soporte de numeración de líneas (`[L1] ...`) y rangos opcionales (`start_line`, `end_line`) en `read_file`.
  - Mejorar `edit_file` con diagnósticos de ocurrencias múltiples o ausencia del texto objetivo.
- **Alternativas consideradas:**
  - *Truncado de cabeza (Head-only):* Rechazado porque descarta la traza de error en salidas de comandos largos.
  - *Truncado de cola (Tail-only):* Rechazado porque descarta encabezados de contexto y parámetros iniciales.

### 6. Inyección Proactiva de Contexto y Observation Masking Efímero
- **Decisión:** En `harness/agent_loop.py`:
  - **Inyección Proactiva:** Al inicializar el bucle, recopilar información ambiental mediante `build_environment_context(cwd)`: Sistema Operativo, directorio de trabajo actual, estado de la rama Git (`git rev-parse`, `git status --short`), árbol de directorios resumido (nivel 1 y 2 ignorando `.git`, `node_modules`, `__pycache__`), y contenido de `JARVIS.md` o `AGENT.md` si existen. Inyectarlo en la cabecera del System Prompt.
  - **Observation Masking Efímero:** En cada turno antes de enviar los mensajes al LLM, generar una copia de trabajo de la lista de mensajes. En los mensajes con `role: "tool"` con antigüedad mayor a 5 pasos respecto al paso actual, enmascarar su contenido con `[Salida anterior de herramienta truncada para optimizar contexto RAM. Usa read_file o reejecuta si necesitas refrescar estos datos.]`.
  - **Integridad de `tool_call_id`:** Mantener siempre sincronizados los `tool_call_id` entre mensajes de asistente y herramientas correspondientes para evitar errores HTTP 400 en APIs estrictas como OpenAI y Groq.
- **Alternativas consideradas:**
  - *Modificar el historial de mensajes original en memoria:* Rechazado porque corrompe la persistencia de sesiones y la trazabilidad de depuración.
  - *Eliminar mensajes antiguos del historial:* Rechazado porque romper la correspondencia `assistant.tool_calls` vs `role: "tool"` genera errores HTTP 400.

## Risks / Trade-offs

- **[Riesgo] Evasión de la whitelist de comandos mediante combinaciones sutiles de sintaxis shell.**
  → *Mitigación:* Se prohíben taxativamente todos los operadores de encadenamiento y redirección (`;`, `&&`, `||`, `|`, `` ` ``, `$()`, `>`, `<`, `\n`). Si se detecta cualquiera de estos caracteres, el comando pierde automáticamente la condición de seguro y exige confirmación `[s/n/a]`.
- **[Riesgo] Bloqueo percibido de la terminal durante Exponential Backoff en errores 429 prolongados.**
  → *Mitigación:* Se imprime un mensaje visual con el tiempo estimado de reintento (`Esperando {delay}s antes de reintentar (intento {attempt}/{max_retries})...`) y se acota el retraso máximo a 60 segundos con un tope de 5 intentos.
- **[Riesgo] Pérdida de datos necesarios si el LLM requiere detalles de una herramienta ejecutada hace más de 5 pasos.**
  → *Mitigación:* El marcador de enmascaramiento informa explícitamente al LLM que los datos fueron archivados para ahorrar RAM cognitiva y le recuerda que puede volver a consultar la herramienta o archivo si lo requiere.
- **[Riesgo] Incompatibilidad de rutas en entornos Windows.**
  → *Mitigación:* Toda manipulación de rutas en `guardrails.py` y `tools.py` se realiza utilizando `pathlib.Path.resolve()` normalizado para evitar diferencias entre separadores `/` y `\`.

## Migration Plan

1. **Fase 1 (Limpieza Runtime & Guardrails):**
   - Actualizar `mcp.json` para eliminar `@modelcontextprotocol/server-filesystem`.
   - Eliminar `package.json` y `package-lock.json`.
   - Refactorizar `harness/guardrails.py` implementando los 3 niveles de riesgo, la whitelist segura y el conjunto de aprobación de sesión.
   - Actualizar `harness/mcp_client.py` con inicialización tolerante a fallos (*graceful degradation*).
2. **Fase 2 (Resiliencia Multi-API):**
   - Refactorizar `harness/llm_provider.py` elevando `max_tokens=4096`, añadiendo Exponential Backoff con jitter y el reparador `repair_json_arguments`.
3. **Fase 3 (Herramientas y Truncado Head+Tail):**
   - Refactorizar `harness/tools.py` implementando `smart_truncate`, rangos/numeración en `read_file` y validación diagnóstica en `edit_file`.
4. **Fase 4 (Inteligencia del Kernel y Contexto):**
   - Refactorizar `harness/agent_loop.py` y `main.py` integrando `build_environment_context`, `apply_observation_masking` en copia efímera y el bucle de auto-reparación ante fallos de herramientas.
5. **Fase 5 (Verificación de Calidad):**
   - Actualizar y ejecutar la suite completa de pruebas unitarias (`tests/test_guardrails.py`, `tests/test_llm_provider.py`, `tests/test_tools.py`, `tests/test_agent_loop.py`).
   - Validar ejecución al 100% con `python -m unittest discover -s tests -p "test_*.py" -v`.
