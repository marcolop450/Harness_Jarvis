# Design

## Context
El sistema Jarvis opera como un agente CLI en terminal con arquitectura modular bajo `harness/`. El bucle REPL actual utiliza `input()` estándar de Python y salidas de texto crudo con caracteres ASCII sencillos (`=====`, `[+]`). Con la incorporación de nuevos flujos interactivos, se requiere una capa visual moderna inspirada en herramientas como OpenCode y Claude Code, manteniendo estricta la separación de responsabilidades exigida por la Constitución del Harness.

## Goals / Non-Goals

**Goals:**
- Proveer una experiencia de terminal de alta gama con menús desplegables de autocompletado al tipear `/` usando `prompt_toolkit`.
- Diseñar paneles estilizados, bordes redondeados Unicode (`╭─╮`), jerarquía semántica de color y spinners no intrusivos usando `rich`.
- Implementar comandos de control agéntico en caliente: `/plan` (Arquitecto vs Actuador), `/steps <n>` (límite dinámico) y `/approval` (política de confirmación).
- Implementar comandos de diagnóstico y observabilidad: `/doctor`, `/tokens`, `/diff`, `/tree` y `/export`.
- Mantener compatibilidad 100% con terminales no interactivas y tuberías (pipes).

**Non-Goals:**
- No se incorporarán frameworks orquestadores pesados (LangChain, CrewAI, AutoGen).
- No se implementarán aplicaciones a pantalla completa excluyentes tipo TUI compleja (`Textual`) que rompan el scroll histórico natural de la terminal.
- No se construirán servidores web o interfaces gráficas de escritorio.

## Decisions

### 1. Librerías de Terminal: `prompt_toolkit` + `rich`
- **Decisión**: Usar `prompt_toolkit.PromptSession` con `WordCompleter` / `NestedCompleter` para capturar la entrada del usuario y autocompletar comandos de barra (`/`). Usar `rich.console.Console` y `rich.panel.Panel` con estilo `rounded` para renderizar el banner, las respuestas estructuradas y el diagnóstico.
- **Razón**: `prompt_toolkit` resuelve de forma robusta en Windows y Linux el historial con flechas arriba/abajo y el autocompletado flotante sin interferir con las secuencias de escape. `rich` ofrece soporte de color TrueColor y degradación automática cuando no hay soporte TTY.
- **Alternativas consideradas**:
  - `Textual`: Requiere un bucle de eventos asíncrono completo que toma control total de la pantalla, perdiendo el formato de CLI estándar de tipo shell.
  - `ANSI crudo`: Altamente propenso a errores entre CMD, PowerShell y emuladores modernos como Windows Terminal.

### 2. Estado de Sesión en Memoria (`SessionRuntime`)
- **Decisión**: Introducir una estructura liviana de estado en `harness/session_state.py` (o dentro del ciclo REPL) que mantenga:
  - `max_steps`: Límite entero dinámico (por defecto 15, configurable entre 1 y 50).
  - `mode`: Enumeración `ACTOR` | `PLAN` (Arquitecto).
  - `approval_policy`: `CONFIRM` (por defecto) | `AUTO`.
  - `file_tracker`: Registro en memoria de archivos leídos y modificados durante la sesión para alimentar `/diff`.
- **Razón**: Permite a los comandos `/steps`, `/plan`, `/approval` y `/diff` actuar de forma cohesiva sin recurrir a variables globales dispersas ni reiniciar procesos.
- **Alternativas consideradas**:
  - Reescribir archivos de configuración en cada comando: Ineficiente y causa efectos colaterales persistentes no deseados.

### 3. Modo Arquitecto (`/plan`)
- **Decisión**: Al activar el modo Arquitecto (`/plan`), el bucle inyecta en el prompt del sistema la directiva de solo lectura y diseño, e intercepta cualquier invocación a `write_file`, `edit_file` o comandos de escritura en `run_command`, retornando un mensaje de advertencia seguro sin modificar el disco.
- **Razón**: Brinda al usuario una forma segura de pedir análisis o arquitecturas complejas a modelos sin riesgo de que alteren código de forma prematura.

### 4. Implementación de Diagnósticos (`/doctor`, `/tokens`, `/diff`, `/tree`, `/export`)
- **`/doctor`**: Evalúa conectividad al endpoint configurado (tiempo de respuesta HTTP), disponibilidad del modelo y estado de los servidores MCP descubiertos.
- **`/tokens`**: Calcula caracteres acumulados en el historial de mensajes, aplica factor de conversión estimado (~4 chars/token) e informa la carga relativa de la ventana de contexto.
- **`/diff`**: Genera un diff unificado (`difflib.unified_diff`) entre el contenido inicial de los archivos antes de la primera edición y su estado actual en disco.
- **`/tree`**: Genera un árbol de hasta 3 niveles de profundidad ignorando patrones comunes (`.git`, `__pycache__`, `node_modules`, `.venv`, `.pytest_cache`).
- **`/export`**: Vuelca el historial de conversación limpio en un archivo Markdown con fecha y metadatos (`sesion_jarvis_YYYYMMDD_HHMMSS.md`).

## Risks / Trade-offs

- **[Riesgo] Rendimiento en terminales Windows CMD heredadas**: `prompt_toolkit` o `rich` podrían mostrar fallos de renderizado en consolas muy antiguas de Windows 7/8.
  - *Mitigación*: Detección de capacidades de terminal (`console.is_terminal`), forzando modo ASCII limpio si no se detecta soporte UTF-8/TrueColor.
- **[Riesgo] Modelos que intentan forzar escritura en modo /plan**: Un LLM podría insistir en llamar a `write_file`.
  - *Mitigación*: El guardrail de `agent_loop.py` bloquea la herramienta en tiempo de despacho y responde con un mensaje `tool` explicativo para auto-corrección sin tocar el disco.

## Migration Plan
1. Agregar `rich>=13.0.0` y `prompt-toolkit>=3.0.0` en `pyproject.toml` y `requirements.txt`.
2. Mantener intactas las firmas públicas de `run_agent_turn` para asegurar retrocompatibilidad con las pruebas existentes.
