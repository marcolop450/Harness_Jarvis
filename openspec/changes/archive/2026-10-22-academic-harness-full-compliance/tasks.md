# Tasks: Cumplimiento Académico Total del Arnés y Optimización de Errores

## 1. Mapeo Limpio de Errores y Control de Tokens (`llm_provider.py`)
- [x] 1.1 Implementar `format_clean_api_error` en `harness/llm_provider.py` para mapear excepciones HTTP (429, 401, 404, 400, 500) a mensajes concisos y claros en una sola línea, eliminando volcados crudos de JSON.
- [x] 1.2 Configurar parámetro preventivo `max_tokens` (1500) en las llamadas a `chat.completions.create` para evitar rebasar límites OTPM en tiers gratuitos como Groq.
- [x] 1.3 Agregar pruebas unitarias en `tests/test_llm_provider.py` para validar la captura y el formateo limpio de errores 429, 401, 404 y 500.

## 2. Autorización por Lote `[s/n/a]` (`guardrails.py`)
- [x] 2.1 Modificar `confirm_action` en `harness/guardrails.py` para ofrecer la opción `a` (*autorizar todo*) y registrar objetivos aprobados en memoria para el turno activo.
- [x] 2.2 Implementar método de limpieza/reinicio de aprobaciones por turno (`clear_turn_approvals()`) invocado al inicio de cada nuevo comando en el CLI.
- [x] 2.3 Agregar pruebas unitarias en `tests/test_guardrails.py` verificando que la opción 'a' autoriza la llamada actual y omite confirmaciones subsiguientes para el mismo objetivo.

## 3. Gestión y Recuperación de Sesiones (`/sessions` y `/resume`)
- [x] 3.1 Implementar módulo/funciones de persistencia de sesiones en `.harness_sessions/` guardando ID, fecha/hora, modelo y lista de mensajes.
- [x] 3.2 Implementar los comandos interactivos `/sessions` (listado ordenado) y `/resume <id>` (reanudación del historial) en `main.py`.
- [x] 3.3 Agregar pruebas unitarias en `tests/test_cli.py` validando el guardado, listado y restauración de sesiones.

## 4. Compactación Inteligente de Contexto (`/compact`)
- [x] 4.1 Implementar la función de compactación en `harness/agent_loop.py` que solicita al LLM un resumen estructurado del historial acumulado y sustituye los turnos intermedios.
- [x] 4.2 Integrar el comando `/compact` en `main.py` con validación de historial mínimo y reporte de reducción.
- [x] 4.3 Agregar pruebas unitarias validando la síntesis y reemplazo seguro del historial de mensajes.

## 5. Medición de Tiempos y Subagente Aislado (`agent_loop.py`)
- [x] 5.1 Agregar medición de tiempo transcurrido por turno (`⏱️ X.XXs`) en `harness/agent_loop.py` e imprimirlo con la respuesta final.
- [x] 5.2 Implementar función de subagente de investigación aislado con contexto limpio y herramientas de solo lectura, retornando solo un resumen final al orquestador.
- [x] 5.3 Agregar pruebas unitarias para la ejecución del subagente aislado y la medición de tiempos.

## 6. Mínimo 3 Herramientas MCP (`tools.py`)
- [x] 6.1 Implementar 3 herramientas bajo el protocolo Model Context Protocol (MCP) en `harness/tools.py`: `mcp_fetch` (consulta HTTP segura), `mcp_git_info` (estado e historial git) y `mcp_sqlite_query` (consultas SQLite).
- [x] 6.2 Definir los esquemas JSON Schema correspondientes y asegurar truncado estricto a 4000 caracteres.
- [x] 6.3 Agregar pruebas unitarias en `tests/test_tools.py` para las 3 herramientas MCP.

## 7. Manual de Defensa Técnica del Arnés (`DEFENSA_HARNESS.md`)
- [x] 7.1 Redactar `DEFENSA_HARNESS.md` con explicación completa de la arquitectura, diagrama de flujo, comparativa vs wrappers simples, desglose de los 4 módulos, justificación de los 3 MCPs, subagentes con contexto aislado y banco de preguntas/respuestas para la defensa individual.

## 8. Verificación Integral y Suite de Pruebas
- [x] 8.1 Ejecutar la suite completa de pruebas unitarias (`python -m unittest discover -s tests -p "test_*.py" -v`) asegurando 100% de éxito.
