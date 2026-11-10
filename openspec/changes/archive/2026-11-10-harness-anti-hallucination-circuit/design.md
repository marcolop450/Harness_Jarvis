# Design: Circuito Anti-Alucinación y Anclaje Fáctico en el Harness

## Context
Ver motivación en `proposal.md`.
El agente interactúa con modelos de lenguaje de diversos tamaños (desde modelos de frontera hasta modelos locales de 7B/9B en LM Studio u Ollama). Los modelos pequeños son propensos al "optimismo ciego": si una herramienta falla o es cancelada por el usuario (HITL), tienden a generar respuestas afirmando falsamente que completaron el objetivo porque no cotejan el resultado contra el estado del disco.

## Goals / Non-Goals

**Goals:**
- Inyectar en el System Prompt de `build_workspace_system_prompt` una directiva inequívoca de Verdad Fáctica (Grounded Truth).
- Enriquecer en `agent_loop.py` la gestión de respuestas de herramientas: si una herramienta devuelve un estado de cancelación (`Acción cancelada`), el mensaje de rol `tool` incluirá un prefijo de advertencia fáctica de sistema `[ESTADO REAL DEL SISTEMA: ACCION CANCELADA]`.
- En `tools.py`, asegurar que `tool_write_file` y `tool_run_command` verifiquen la existencia real del archivo o directorio tras operaciones de escritura antes de reportar éxito.

**Non-Goals:**
- No alterar la ventana de contexto de los modelos ni modificar la biblioteca de prompts de usuario.
- No modificar el algoritmo de streaming de proveedores.

## Decisions

### 1. Inyección de Verdad Fáctica en el Contexto del Espacio de Trabajo
- **Decisión:** Añadir a `build_workspace_system_prompt` (en `harness/model_config.py` o `agent_loop.py`) una sección explícita:
  ```markdown
  ## PRINCIPIO DE VERDAD FÁCTICA (ANTI-ALUCINACIÓN):
  1. NUNCA asumas que un archivo o carpeta existe a menos que una herramienta te haya confirmado su creación con éxito en este turno.
  2. Si una herramienta devuelve "Acción cancelada" o un error, NUNCA digas que el paso fue completado. Reconoce de inmediato ante el usuario que la operación fue abortada.
  3. Si dudas de la existencia de un archivo o directorio, usa 'list_dir' o 'read_file' antes de emitir tu conclusión.
  ```
- **Alternativa descartada:** Confiar en que el modelo entienda el JSON Schema sin directivas en el system prompt (demostró fallar con Qwen 9B).

### 2. Prefijo Fáctico en Observaciones Canceladas (`agent_loop.py`)
- **Decisión:** Cuando `result_text` en `agent_loop.py` comience con `Acción cancelada:`, estructurar el contenido de `tool` con una alerta reforzada:
  `[ALERTA DE SEGURIDAD Y ESTADO REAL: La operación fue cancelada por el usuario. Los archivos/comandos NO existen ni fueron ejecutados. Reporta este estado honestamente.]`
- **Alternativa descartada:** Detener abruptamente el bucle y no dejar que el LLM responda (perjudica la naturalidad de la conversación).

### 3. Verificación Post-Escritura en Herramientas Nativas
- **Decisión:** En `tool_write_file`, tras escribir en disco, verificar explícitamente `safe_path.exists()` y `safe_path.stat().st_size > 0` antes de emitir el mensaje de éxito.

## Risks / Trade-offs
- **[Riesgo]** Incremento leve de tokens en el System Prompt (~80 tokens).
  - *Mitigación:* Se compensa ampliamente evitando bucles de auto-engaño donde el modelo intenta operar sobre archivos inexistentes consumiendo cientos de tokens innecesarios.
