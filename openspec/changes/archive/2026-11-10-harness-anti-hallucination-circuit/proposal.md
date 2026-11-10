# Proposal: Circuito Anti-Alucinación y Anclaje Fáctico en el Harness

## Why
Durante la ejecución del agente con modelos locales o pequeños (ej. Qwen 9B en LM Studio), si el usuario rechaza una acción de consola o escritura (HITL) o si una herramienta falla, el modelo ignora el resultado negativo y alucina en su respuesta textual afirmando falsamente que los archivos y carpetas fueron creados ("Paso 1 Completado"). Es crítico blindar el circuito del Harness (`agent_loop.py`, `workspace-context`, `tools.py`) para obligar al modelo a anclarse en la verdad fáctica del entorno y prohibir afirmaciones falsas de éxito.

## What Changes
- Inyección en el `workspace-context` (System Prompt) de una directiva obligatoria de **Verdad Fáctica (Grounded Truth)**: el modelo solo puede dar por completadas acciones cuya herramienta haya devuelto éxito verificable; si una acción es cancelada o falla, debe reconocer el estado real y no mentir.
- Intercepción en `agent_loop.py` de tool calls canceladas o fallidas: si una herramienta devuelve cancelación de usuario, el arnés inyecta una advertencia de sistema fáctica obligando al LLM a reconocer que no hubo cambios en el disco.
- Verificación fáctica en herramientas de creación (`tools.py`): las herramientas validan la existencia real del archivo o directorio tras su ejecución antes de emitir confirmación de éxito.

## Capabilities

### Modified Capabilities
- `agent-loop`: Manejo e inyección de advertencias de anclaje fáctico cuando una herramienta es rechazada o falla, impidiendo que el modelo alucine éxito en turnos subsiguientes.
- `workspace-context`: Regla constitucional de verdad fáctica (Grounded Truth) inyectada en el prompt ambiental para modelos de lenguaje locales y de nube.

## Impact
- Afecta a `harness/agent_loop.py`, `harness/model_config.py` y `harness/tools.py`.
- No introduce dependencias externas ni rompe compatibilidad con comandos slash existentes.
- Queda fuera de alcance: alterar el parser de modelos o modificar la ventana de contexto base.
