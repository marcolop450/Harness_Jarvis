# Design: Directiva de Acción Inmediata (Bias for Action), Autocompletado Avanzado y Renovación de UX

## Context
Ver motivación en `proposal.md`.
Modelos con estilo conversacional como Meta Muse Spark o Qwen tienden a responder afirmativamente en texto ("Claro, ahora mismo modifico el archivo...") sin emitir llamadas a herramientas en el mismo turno. Además, varias secciones de la CLI aún usaban impresiones con cajas de texto ASCII rudimentarias y el autocompletador de `prompt_toolkit` solo reconocía la palabra inicial del comando.

## Goals / Non-Goals

**Goals:**
- Configurar un `DEFAULT_BASE_PROMPT` con una directiva enfática de ingeniería agéntica ("Bias for Action").
- Incorporar en `agent_loop.py` una detección de respuestas de falsa completación / promesa sin herramientas, reinyectando una instrucción de acción inmediata si el usuario pidió editar archivos.
- Mejorar `JarvisCommandCompleter` en `harness/cli.py` para admitir subcomandos (`add`, `rm`, `list`, `auto`, `confirm`, `reconnect`, etc.) y autocompletado de archivos locales.
- Crear en `harness/ui.py` una función `print_rich_user_guide()` con paneles Rich categorizados y usarla en `/guide` y `/help`.
- Reemplazar las cajas ASCII restantes en `main.py` (`/sessions`, `/compact`, `/key`, `/endpoint`, `/model list`) con componentes Rich.

**Non-Goals:**
- No implementar una TUI de pantalla completa con Textual (el usuario trabaja en consola tipo Claude Code con streaming continuo).
- No eliminar el fallback a `DummyOutput` para entornos no interactivos o pytest.

## Decisions

### 1. Directiva "Bias for Action" y Nudge en Bucle
- **Decisión:** Enriquecer `DEFAULT_BASE_PROMPT` con la instrucción: "NUNCA respondas con frases conversacionales como 'Entendido, voy a modificar...' sin invocar la herramienta en el mismo paso. Si el usuario pide crear o modificar código, tu primer deber es emitir 'write_file' o 'edit_file'".
- En `agent_loop.py`: si el usuario pidió modificar/crear un archivo y la respuesta del modelo no contiene `tool_calls` pero contiene frases típicas de procrastinación ("ahora sí lo mejoro", "voy a modificar", "procedo a editar"), el bucle no termina: inyecta un mensaje de sistema temporal de corrección y da un paso adicional para que el LLM ejecute la tool.

### 2. Autocompletador Jerárquico en `harness/cli.py`
- **Decisión:** Extender `JarvisCommandCompleter` para que inspeccione `document.text_before_cursor`.
  - Si empieza con `/model `: autocompleta `list`, `add`, `rm`.
  - Si empieza con `/approval `: autocompleta `confirm`, `auto`.
  - Si empieza con `/mcp `: autocompleta `reconnect`.
  - Si el argumento parece una ruta o el comando es general: sugiere archivos de la carpeta actual mediante `Path(cwd).glob(...)`.

### 3. Guía Rica y Paneles Semánticos
- **Decisión:** En `harness/ui.py`, estructurar la guía usando `rich.panel.Panel` y `rich.table.Table` con colores temáticos:
  - Cyan: Control y navegación
  - Verde: Modelos y proveedores
  - Amarillo: Seguridad y aprobación
  - Magenta: MCP y herramientas

## Risks / Trade-offs
- **[Riesgo]** Nudge falso positivo si el usuario hace una pregunta sobre código sin pedir cambios.
  - *Mitigación:* La detección de procrastinación solo se activa si el texto del asistente promete explícitamente una acción inminente de modificación ("ahora sí", "voy a editar", "voy a modificar") y el prompt del usuario contenía palabras de acción ("crea", "modifica", "mejora", "edita", "cambia").
