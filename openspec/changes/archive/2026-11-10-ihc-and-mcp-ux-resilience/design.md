# Diseño Técnico: Resiliencia de IHC, Desacoplamiento de Spinner y MCP Silencioso

## 1. Arquitectura de Desacoplamiento del Spinner

### Problema Actual
`main.py` envuelve `run_turn` completamente dentro de:
```python
with compact_spinner("Jarvis está procesando tu solicitud..."):
    reply, conversation_history = run_turn(...)
```
`run_turn` llama a `run_agent_loop`, que ejecuta:
- LLM inference (lento, IO bound).
- Tool calls -> `execute_tool` -> `confirm_action` -> `input()` (bloqueante para interacción humana).

El hilo en segundo plano de Rich redibuja la animación mientras `input()` espera teclas del usuario, corrompiendo la terminal.

### Solución Diseñada
1. En `main.py`, eliminar el spinner global que envuelve a `run_turn`.
2. En `harness/agent_loop.py`, envolver la llamada al modelo `caller(...)` en un hook o spinner efímero controlado.
   - Si se ejecuta interactivamente (terminal TTY), mientras el LLM razona se muestra el spinner.
   - En cuanto `caller(...)` devuelve la respuesta, el spinner se cierra limpiamente antes de iterar sobre `response.tool_calls`.
   - Así, cuando cualquier herramienta nativa o MCP invoque `confirm_action`, la consola estará completamente en reposo, permitiendo una experiencia de entrada pura, visible y responsiva.

## 2. Protocolo de Feedback Visual en `confirm_action` (Guardrails)

```python
# Al esperar la confirmación:
prompt_text = "¿Desea autorizar esta operacion? [s = sí / n = no / a = siempre]: "
answer = prompter(prompt_text).strip().lower()

# Si autoriza:
print("[✓] Operación autorizada por el usuario. Ejecutando...")

# Si rechaza o presiona Enter sin escribir 's':
print("[x] Operación cancelada por el usuario. No se realizaron cambios.")
```

## 3. Retornos de Herramienta Anti-Alucinación (`harness/tools.py`)

Cuando `confirm_action` devuelve `False`:
```python
return (
    f"Operación CANCELADA por el usuario: Se denegó la ejecución del comando '{command}'. "
    "El comando NO fue ejecutado y NO se realizaron cambios en el disco. "
    "No asumas que los archivos o carpetas existen."
)
```

## 4. MCP Logging Silencioso (`harness/mcp_client.py`)

Cambiar:
`logger.warning("Servidor MCP '%s' no disponible...", config.name)`
a:
`logger.debug("Servidor MCP '%s' no disponible...", config.name)`

El reporte completo de disponibilidad de servidores MCP permanece intacto para los comandos `/mcp`, `/mcp reconnect` y `/doctor`.

## 5. Visualización Mejorada de `/tree` (`harness/cli.py`)

Asegurar que subcarpetas vacías muestren `(vacío)` para dar plena certeza al usuario sobre el estado de su estructura de directorios.
