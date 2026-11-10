# Tasks: Implementación del Arnés Jarvis a Grado de Producción

## 1. Limpieza de Runtime MCP y Tolerancia a Fallos

- [x] 1.1 Limpiar `mcp.json` para retirar `@modelcontextprotocol/server-filesystem` y eliminar `package.json`/`package-lock.json`, verificando la ausencia de archivos npm residuales y que solo queden configurados `fetch` y `git`.
- [x] 1.2 Implementar arranque con degradación elegante (*graceful degradation*) en `harness/mcp_client.py` ante servidores MCP que fallen o no estén instalados, y verificar mediante test unitario que Jarvis continúa su inicio normal sin interrumpir el CLI.

## 2. Gobernanza de Seguridad Smart HITL en 3 Niveles

- [x] 2.1 Refactorizar `harness/guardrails.py` para implementar la clasificación en 3 niveles de riesgo (Nivel 0 auto-aprobado para lectura, Nivel 1 para escritura en workspace con memoria `[a]`, Nivel 2 para comandos y red) e integrar `authorize_and_dispatch`, verificando con pruebas unitarias en `tests/test_guardrails.py`.
- [x] 2.2 Implementar en `harness/guardrails.py` la validación estricta de la whitelist de comandos seguros y el bloqueo sin excepciones de operadores de encadenamiento o redirección shell (`;`, `&&`, `||`, `|`, `` ` ``, `$()`, `>`, `<`, `\n`), verificando con pruebas unitarias de inyección en `tests/test_guardrails.py`.
- [x] 2.3 Implementar el soporte para el conjunto de objetivos aprobados de sesión (`session_approved_targets: set[str]`) en `harness/guardrails.py` y verificar que la opción `[a]` suprime solicitudes repetidas para el mismo archivo en `tests/test_guardrails.py`.

## 3. Resiliencia Multi-API y Auto-reparación

- [x] 3.1 Actualizar `harness/llm_provider.py` para fijar `max_tokens=4096` e implementar Exponential Backoff con jitter y lectura de cabecera `Retry-After` ante errores HTTP 429, verificando con pruebas unitarias simuladas de reintento en `tests/test_llm_provider.py`.
- [x] 3.2 Implementar `repair_json_arguments` en `harness/llm_provider.py` para sanitizar bloques markdown, comas finales y comillas no escapadas en `tool_calls`, y verificar con suite de casos de prueba de JSONs malformados en `tests/test_llm_provider.py`.

## 4. Herramientas Nativas con Truncado Head+Tail

- [x] 4.1 Implementar `smart_truncate` (1000 cabeza + 3000 cola = 4000 caracteres con marcador explícito) en `harness/tools.py` y aplicarlo a todas las salidas de herramientas, verificando con pruebas unitarias en `tests/test_tools.py`.
- [x] 4.2 Enriquecer `read_file` con soporte opcional de rango de líneas y prefijos `[L1]` y `edit_file` con diagnósticos de ocurrencias múltiples o ausencia del objetivo en `harness/tools.py`, verificando con pruebas unitarias en `tests/test_tools.py`.

## 5. Inteligencia del Kernel y Gestión de Memoria

- [x] 5.1 Implementar `build_environment_context` en `harness/agent_loop.py` para inyectar proactivamente SO, cwd, estado de Git, árbol raíz y reglas `JARVIS.md`/`AGENT.md` en el System Prompt, verificando que el prompt generado contenga todos los bloques contextuales en `tests/test_agent_loop.py`.
- [x] 5.2 Implementar Observation Masking efímero en `harness/agent_loop.py` para enmascarar llamadas de herramientas con más de 5 pasos de antigüedad preservando los `tool_call_id` y sin alterar el historial persistido de sesión, verificando con pruebas unitarias en `tests/test_agent_loop.py`.
- [x] 5.3 Implementar el bucle de auto-reparación (Self-Healing) en `harness/agent_loop.py` para devolver errores estructurados como mensajes `role: "tool"` cuando un comando o JSON falle sin abortar la ejecución, verificando con pruebas unitarias en `tests/test_agent_loop.py`.

## 6. Verificación de Integración de Sistema

- [x] 6.1 Ejecutar la suite completa de pruebas unitarias (`python -m unittest discover -s tests -p "test_*.py" -v`) verificando que el 100% de los tests pasen exitosamente.
- [x] 6.2 Validar la ejecución del binario / CLI `jarvis` o `python main.py --help` verificando el inicio limpio con el nuevo contexto de entorno y sin advertencias bloqueantes.
