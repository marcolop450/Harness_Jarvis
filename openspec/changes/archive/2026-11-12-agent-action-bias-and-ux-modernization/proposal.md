# Proposal: Directiva de Acción Inmediata (Bias for Action), Autocompletado Avanzado y Renovación de UX

## Why
Modelos de lenguaje orientados a conversación (como Meta Muse Spark o Qwen) sufren de "chat laziness" / procrastinación conversacional: responden frases como "Entendido, voy a modificar el archivo..." o "Ahora sí lo mejoro..." sin invocar la herramienta (`write_file` o `edit_file`) en el mismo turno, provocando que el arnés termine la ejecución sin aplicar cambios en disco. Asimismo, la guía (`/guide`) conserva texto ASCII plano desactualizado sin los nuevos comandos (/plan, /approval, /doctor, etc.), el autocompletador no cubre subcomandos ni archivos locales, y persisten cajas visuales antiguas en comandos de sesión.

## What Changes
- **Directiva de Acción Inmediata (Bias for Action):** Refuerzo del System Prompt base y salvaguarda en `agent_loop.py` que detecta respuestas puramente conversacionales que prometen acciones sin emitir herramientas cuando se solicitó una modificación, reenviando un estímulo correctivo inmediato de ejecución.
- **Autocompletado Contextual Avanzado (`harness/cli.py`):** Expansión del autocompletador para sugerir subcomandos (`/model add`, `/approval auto`, `/mcp reconnect`) y nombres de archivos locales del espacio de trabajo.
- **Renovación Visual de la Guía y Mensajes (`main.py` y `harness/ui.py`):** Reemplazo de `print_user_guide` con paneles Rich estilizados con bordes redondeados `╭─╮` categorizados por función, y modernización de las tablas de `/sessions` y mensajes de `/compact` y `/key`.

## Capabilities

### Modified Capabilities
- `agent-loop`: Detección y prevención de procrastinación conversacional (promesas de acción sin invocar herramientas).
- `cli-entrypoint`: Autocompletado enriquecido de subcomandos y archivos, junto con la modernización visual integral de `/guide` y paneles interactivos.

## Impact
- Afecta a `main.py`, `harness/agent_loop.py`, `harness/cli.py`, `harness/model_config.py` y `harness/ui.py`.
- No requiere librerías externas adicionales (aprovecha `rich` y `prompt_toolkit` ya instalados).
- 100% retrocompatible con todos los flujos existentes.
