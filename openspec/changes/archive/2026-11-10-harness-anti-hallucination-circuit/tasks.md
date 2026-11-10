# Tasks

## 1. Directiva de Verdad Fáctica en el Contexto del Entorno

- [x] 1.1 Inyectar en `build_workspace_system_prompt` (`harness/model_config.py`) el bloque normativo de Verdad Fáctica (Grounded Truth) prohibiendo reportar como completadas acciones canceladas o fallidas, y verificar con pruebas unitarias en `test_model_config.py`.
- [x] 1.2 Incorporar en `build_environment_context` (`harness/agent_loop.py`) la regla fáctica que ordena al LLM usar `list_dir` o `read_file` antes de emitir afirmaciones sobre archivos o directorios nuevos.

## 2. Intercepción y Anclaje Fáctico en el Bucle del Agente

- [x] 2.1 Modificar en `harness/agent_loop.py` la recepción de resultados de herramientas para detectar cancelaciones (`Acción cancelada`) y anteponer una directiva fáctica estricta en el mensaje de rol `tool`.
- [x] 2.2 Agregar prueba unitaria en `tests/test_agent_loop.py` verificando que un resultado de herramienta cancelado incluye la advertencia fáctica de sistema.

## 3. Verificación Post-Escritura en Herramientas Nativas

- [x] 3.1 Actualizar `tool_write_file` en `harness/tools.py` para validar la existencia física (`safe_path.exists()`) antes de retornar el mensaje de éxito.
- [x] 3.2 Verificar con pruebas en `tests/test_tools.py` que una escritura fallida no emite falsos positivos de éxito.

## 4. Verificación Integral y Suite de Regresión

- [x] 4.1 Ejecutar la suite completa de pruebas (`pytest`) asegurando el 100% de tests en verde sin regresiones.
