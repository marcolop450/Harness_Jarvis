# GUÍA MAESTRA DE DEFENSA TÉCNICA: ARQUITECTURA DE ARNESES (HARNESS) DE IA
**Proyecto:** Harness Jarvis CLI (Estilo Claude Code / OpenCode)  
**Evaluación:** Examen Oral y Defensa Individual de Arquitectura  

---

## 1. La Fórmula del Sistema (El Fundamento Esencial)

Si el profesor pregunta: **"¿Qué es un Harness y cuál es su fórmula?"**  
**Respuesta verbal inmediata:**
> *"Un Harness no es un simple wrapper de un chatbot. Un Harness es un entorno de ejecución estructurado y seguro que gobierna a un modelo de lenguaje. Nuestra arquitectura se rige por la fórmula:*  
> **Harness = Modelo (Adaptador Multi-API) + Reglas (System Prompt y Guardrails) + Contexto (CWD y AGENT.md) + Herramientas (Tools con JSON Schema y MCP)**"

### ¿Por qué NO es un simple wrapper?
| Característica | Wrapper Simple (Chatbot) | Harness de IA (Jarvis) |
| :--- | :--- | :--- |
| **Flujo de Ejecución** | Lineal (1 pregunta $\rightarrow$ 1 respuesta). | Ciclo ReAct iterativo (`while` acotado a `MAX_STEPS = 15`). |
| **Interacción con el Sistema** | Nula o sin control de seguridad. | Despacho de herramientas con esquemas JSON Schema rigurosos. |
| **Seguridad Activa** | Inexistente (puede leer cualquier archivo). | **Guardrails**: bloqueo total de `.env`, anti-path traversal y confirmación humana interactiva `[s/n/a]`. |
| **Control de Contexto** | Acumulación indiscriminada de tokens. | Compactación semántica (`/compact`), catálogo de sesiones (`/sessions`, `/resume`) y subagentes aislados. |
| **Protocolo de Extensión** | Código ad-hoc no estandarizado. | Soporte nativo para herramientas bajo el estándar **Model Context Protocol (MCP)**. |

---

## 2. Separación Modular Estricta en 4 Módulos (`harness/`)

El sistema organiza toda la lógica central de forma modular y desacoplada:

```
harness/
├── llm_provider.py    # Único punto de conexión con APIs externas
├── agent_loop.py      # Ciclo reactivo while (MAX_STEPS=15) y subagentes
├── tools.py           # Herramientas operativas y 3 clientes MCP
└── guardrails.py      # Seguridad: .env, cwd y confirmación [s/n/a]
```

### 1) `harness/llm_provider.py` (Adaptador Multi-API y Formateo Limpio)
- **Propósito:** Desacopla al agente del proveedor subyacente. Utiliza el cliente universal compatible con OpenAI para conectarse transparentemente a **OpenAI**, **Gemini**, **Groq**, **OpenRouter** y **Ollama local**.
- **Normalización:** Convierte cualquier respuesta externa y sus llamadas a funciones en objetos tipados unificados: `NormalizedResponse` y `NormalizedToolCall`.
- **Mapeador Universal de Errores Limpios (`format_clean_api_error`):** Intercepta excepciones de red y códigos de estado HTTP de los proveedores, transformándolos en mensajes directos de una sola línea sin volcados de JSON:
  - `[Error 429]`: Límite de tokens/cuota agotado en el proveedor.
  - `[Error 401]`: Clave de API inválida o no configurada.
  - `[Error 404]`: Modelo no existente en el proveedor.
  - `[Error 400]`: Solicitud o formato rechazado.
  - `[Error 50x]`: Servicio del proveedor temporalmente fuera de línea.
- **Control Preventivo de Tokens:** Configura `max_tokens = 1500` por llamada para evitar desbordar límites estrictos como las 1000 OTPM de tiers gratuitos de Groq.

### 2) `harness/agent_loop.py` (Ciclo ReAct, Subagentes y Tiempos)
- **Límite Inamovible:** `MAX_STEPS = 15`. Si un modelo entra en un bucle repetitivo de llamadas a herramientas, el contador de pasos lo interrumpe obligatoriamente al llegar a 15, garantizando que el proceso nunca quede bloqueado ni consuma presupuesto infinito.
- **Cronometraje de Turno:** Mide el tiempo de ejecución con `time.perf_counter()` y reporta la latencia real al usuario (`[⏱️ 2.45s]`).
- **Subagente Especializado Aislado (`run_subagent` - Figura 1 del PDF):**
  - Cuando se delega una investigación en el código, el subagente se ejecuta en un contexto limpio (sin el historial del diálogo padre).
  - Solo tiene acceso a herramientas de solo lectura (`read_file`, `list_dir`, `search_code`).
  - Límite estricto de pasos: `MAX_SUBAGENT_STEPS = 5`.
  - Retorna **únicamente el resumen final** al orquestador principal, evitando contaminar y saturar la ventana de tokens del contexto padre.
- **Compactación Inteligente (`compact_conversation_history`):** Mediante `/compact`, resume semánticamente las conversaciones largas conservando decisiones técnicas y reduciendo hasta un 80% los tokens acumulados.

### 3) `harness/tools.py` (Catálogo de Herramientas y Mínimo 3 MCPs)
- **Truncado de Seguridad:** Toda salida generada por cualquier herramienta se trunca estrictamente a **4000 caracteres** (`truncate_output`) para proteger la ventana de contexto contra comandos o archivos gigantes.
- **Clasificación de Riesgo:**
  - `AUTO`: Ejecución inmediata si pasa los guardrails (`read_file`, `list_dir`, `search_code`, herramientas MCP de consulta).
  - `CONFIRM`: Operaciones destructivas o de modificación que exigen confirmación humana interactiva (`write_file`, `edit_file`, `run_command`).
- **3 Integraciones Model Context Protocol (MCP):**
  1. `mcp_fetch`: Protocolo MCP para consultar APIs REST, endpoints o páginas web externas con validación de URL y extracción limpia.
  2. `mcp_git_info`: Inspector MCP de control de versiones (`status`, `log`, `diff`, `branch`) para que el agente entienda el estado del repositorio.
  3. `mcp_sqlite_query`: Motor MCP para bases de datos SQLite locales o en memoria, permitiendo persistir y consultar datos estructurados del proyecto.

### 4) `harness/guardrails.py` (Seguridad No Negociable)
- **Bloqueo Absoluto de `.env` y Secretos:** Detección basada en patrones (`.env`, `*.key`, `id_rsa*`, `.git/config`, etc.). Lanza `SecurityViolationError` de forma inmediata.
- **Anti-Path Traversal:** Verifica con `resolve()` y `relative_to(cwd)` que ninguna ruta relativa ni absoluta escape del directorio de trabajo activo.
- **Confirmación Interactiva `[s/n/a]`:**
  - Despliegue con volcado forzado (`sys.stdout.flush()`).
  - Opción `a` (*autorizar todo*): Registra la ruta del archivo en memoria para el turno activo, evitando preguntar 5 veces consecutivas cuando el modelo genera y edita el mismo archivo en pasos sucesivos.

---

## 3. Gestión y Catálogo de Sesiones (`/sessions` y `/resume`)

> **Nota para la defensa:** Durante las primeras presentaciones, el profesor penalizó la falta de visibilidad y recuperación de sesiones históricas.

### ¿Cómo funciona en nuestro arnés?
1. Cada sesión completada en el espacio de trabajo se almacena en el directorio `.harness_sessions/<session_id>.json` con metadatos: ID, fecha/hora, modelo utilizado y lista ordenada de mensajes.
2. **Comando `/sessions`:** Despliega una tabla formateada en consola con las sesiones guardadas en la carpeta activa, su fecha y cantidad de mensajes.
3. **Comando `/resume <session_id>`:** Carga el archivo JSON correspondiente, restaura el historial en memoria y reactiva el modelo con el que se operó, permitiendo retomar el trabajo exactamente donde se dejó.

---

## 4. Preguntas Frecuentes del Profesor y Cómo Responderlas

### P1: "¿Por qué dividieron el sistema en 4 archivos dentro de `harness/` y no lo hicieron todo en uno solo?"
> **Respuesta:** *"Por el Principio de Responsabilidad Única (SRP) y la arquitectura constitucional del arnés. `llm_provider.py` es el único que conoce las APIs externas; si mañana OpenAI cambia su SDK, solo se modifica ese archivo. `agent_loop.py` gobierna la máquina de estados del bucle reactivo. `tools.py` define las capacidades operativas con esquemas JSON Schema. Y `guardrails.py` actúa como una capa de seguridad ortogonal e infranqueable que intercepta las herramientas antes de tocar el sistema operativo."*

### P2: "¿Cómo evitan que el modelo de lenguaje borre el disco duro o lea credenciales privadas?"
> **Respuesta:** *"Implementamos 3 niveles de defensa en `guardrails.py`:*  
> *1. **Validación de Contención (Anti-Path Traversal):** Toda ruta se resuelve respecto al directorio de trabajo actual (`cwd`). Rutas como `../../Windows` o `/etc/passwd` son bloqueadas antes de ejecutarse.*  
> *2. **Lista Negra de Archivos Confidenciales:** Bloqueo incondicional de cualquier archivo `.env`, claves privadas SSH (`id_rsa`), certificados o configuraciones sensibles.*  
> *3. **Confirmación Humana Interactiva (Human-in-the-Loop):** Toda herramienta de riesgo clasificada como `CONFIRM` (`write_file`, `edit_file`, `run_command`) detiene la ejecución y exige autorización explícita `[s/n/a]` en la terminal antes de efectuar cambios."*

### P3: "¿Qué pasa si el modelo alucina y entra en un bucle infinito llamando a herramientas?"
> **Respuesta:** *"El bucle while en `agent_loop.py` tiene un límite inamovible de `MAX_STEPS = 15`. Cada invocación de herramienta consume un paso. Si al paso 15 el modelo no ha emitido una respuesta final de texto, el ciclo se interrumpe inmediatamente y devuelve un mensaje de corte al usuario, protegiendo tanto la máquina como los tokens de la cuenta."*

### P4: "¿Qué es MCP y cómo está implementado en su código?"
> **Respuesta:** *"Model Context Protocol (MCP) es un estándar abierto promovido por la industria para conectar modelos de IA con fuentes de datos externas y herramientas de forma tipada e interoperable. En `harness/tools.py` implementamos 3 conectores MCP:*  
> *1. `mcp_fetch`: Peticiones HTTP seguras para consultar APIs y recursos web.*  
> *2. `mcp_git_info`: Inspección estructurada del control de versiones (status, ramas, commits y diffs).*  
> *3. `mcp_sqlite_query`: Ejecución de consultas SQL sobre bases de datos locales o en memoria.*  
> *Todas siguen la especificación JSON Schema estricta y cuentan con truncado automático a 4000 caracteres."*

### P5: "¿Por qué implementaron una arquitectura de subagentes con contexto aislado?"
> **Respuesta:** *"Siguiendo la Figura 1 del informe académico, cuando el orquestador principal necesita investigar código o explorar el árbol de archivos, delegar esa tarea a un subagente aislado (`run_subagent`) evita saturar la ventana de tokens. El subagente opera en un contexto limpio con herramientas exclusivas de lectura y devuelve únicamente un extracto con los hallazgos esenciales al agente principal. Esto reduce drásticamente el consumo de tokens y previene el error 429 (Rate Limit)."*

### P6: "¿Cómo resolvieron el problema de las confirmaciones repetitivas y los errores 429 en Groq?"
> **Respuesta:** *"Para las confirmaciones repetitivas, implementamos la opción `a` (*autorizar todo*) en `confirm_action`: al pulsar `a`, el arnés recuerda la aprobación para ese archivo durante el turno activo. Para los errores 429 de cuota o tokens, establecimos un tope preventivo de `max_tokens = 1500`, creamos el comando `/compact` para resumir el historial cuando crece, y construimos `format_clean_api_error` para que, en caso de cualquier eventualidad, la consola informe un mensaje limpio y conciso en lugar de un volcado ininteligible de JSON."*

---

## 5. Resumen de Comandos del CLI para la Demostración en Vivo

| Comando | Función en la Demostración |
| :--- | :--- |
| `/guide` | Muestra la guía rápida fuera de línea para nuevos usuarios (funciona sin API). |
| `/model` | Despliega el catálogo interactivo de modelos registrados y su estado. |
| `/model add <prov> <mod>` | Registra dinámicamente un nuevo modelo y lo persiste en `.harness_models.json`. |
| `/key <prov> <clave>` | Inyecta en vivo y guarda en `.env` la clave de API. |
| `/sessions` | Lista las sesiones previas almacenadas en `.harness_sessions/`. |
| `/resume <id>` | Reanuda una sesión histórica restaurando su historial y configuración. |
| `/compact` | Condensa semánticamente el historial de conversación reduciendo el uso de tokens. |
| `/clear` | Limpia la pantalla y redibuja el encabezado visual. |
| `/reset` | Reinicia la memoria de conversación de la sesión en curso. |
