# Propuesta: Resiliencia de IHC, Desacoplamiento de Spinner y MCP Silencioso

## 1. Justificación y Diagnóstico
Durante la interacción con el usuario en la CLI de Jarvis, se identificaron tres fallas críticas de Interacción Humano-Computadora (IHC) y experiencia de usuario (UX):
1. **Spam constante de MCP en cada consulta:** Cada turno de conversación ejecutaba `definitions()` y disparaba `logger.warning("Servidor MCP 'git' no disponible...")`, saturando la pantalla de advertencias innecesarias cuando el workspace no es un repositorio Git.
2. **Colisión del Spinner en Vivo con HITL (`confirm_action`):** El contexto `compact_spinner` envolvía toda la ejecución del turno (`run_turn`). Cuando una herramienta de riesgo (como `run_command` o `write_file`) solicitaba autorización humana interactiva mediante `input()`, el hilo del spinner de Rich seguía redibujando caracteres en la terminal sobre el prompt de confirmación. Esto impedía visualizar la entrada del usuario, desorientaba el foco de la terminal y provocaba cancelaciones accidentales por pulsaciones de Enter en blanco sin ningún mensaje de feedback en pantalla.
3. **Alucinación del LLM por falta de feedback negativo en Tool Cancellation:** Al cancelarse la confirmación, la herramienta devolvía un string breve que modelos pequeños locales (como Qwen) malinterpretaban como éxito, engañando al usuario al afirmar "Paso 1 Completado - Archivos creados" cuando en realidad el disco estaba intacto.
4. **Visibilidad de carpetas en `/tree`:** El usuario no veía carpetas en el árbol porque nunca llegaron a crearse debido a la cancelación silenciosa del comando `mkdir`.

## 2. Alcance de los Cambios
1. **MCP (`harness/mcp_client.py`):** Cambiar los logs de advertencia de servidores MCP desconectados a nivel `DEBUG` para que no contaminen la pantalla en turnos normales. El estado detallado solo se reporta al ejecutar `/mcp` o `/doctor`.
2. **IHC & Guardrails (`harness/guardrails.py`):**
   - Brindar retroalimentación visual inmediata tras responder a la confirmación interactiva (`[✓] Operación autorizada` vs `[x] Operación cancelada por el usuario`).
   - Mejorar el texto del prompt indicando claramente las opciones disponibles `[s = sí / n = no / a = autorizar en toda la sesión]`.
3. **Desacoplamiento de Spinner (`harness/agent_loop.py` y `main.py`):**
   - El spinner de Rich debe correr únicamente durante la inferencia del modelo LLM (`caller(...)`), deteniéndose antes de procesar llamadas a herramientas (`tool_calls`), garantizando que la terminal esté libre e interactiva para `confirm_action`.
4. **Resistencia a alucinaciones en herramientas (`harness/tools.py`):**
   - Enriquecer el mensaje de cancelación de herramientas para advertir explícitamente al LLM que la acción fue rechazada, ningún comando o archivo fue tocado y no debe alucinar estados inexistentes.
5. **Verificación visual de `/tree` (`harness/cli.py`):**
   - Mostrar indicador explícito cuando un directorio esté vacío.
