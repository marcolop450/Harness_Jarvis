# Tasks

## 1. Dependencias y Estado de Sesión en Memoria

- [x] 1.1 Agregar dependencias `rich>=13.0.0` y `prompt-toolkit>=3.0.0` en `pyproject.toml` y `requirements.txt`, y verificar importación limpia en Python.
- [x] 1.2 Implementar `harness/session_state.py` para gestionar `SessionRuntime` (`max_steps`, `mode`, `approval_policy`, `modified_files`) y verificar con pruebas unitarias en `tests/test_session_state.py`.

## 2. Soporte en el Ciclo Agéntico y Guardrails

- [x] 2.1 Modificar `harness/agent_loop.py` para admitir límite dinámico de pasos desde `SessionRuntime` y verificar con pruebas de corte de iteración en `tests/test_agent_loop.py`.
- [x] 2.2 Integrar el modo Arquitecto (`mode="PLAN"`) en `harness/agent_loop.py` para bloquear escrituras y verificar con prueba de interceptación en `tests/test_plan_mode.py`.
- [x] 2.3 Conectar la política de aprobación en caliente (`CONFIRM` vs `AUTO`) en `harness/guardrails.py` y verificar la conmutación sin confirmación interactiva en `tests/test_guardrails_policy.py`.

## 3. Comandos de Control y Observabilidad

- [x] 3.1 Implementar comandos `/plan`, `/steps` y `/approval` en `harness/cli.py` y verificar el cambio de estado con pruebas en `tests/test_cli_commands.py`.
- [x] 3.2 Implementar comandos `/tokens` y `/export` en `harness/cli.py` y verificar la estimación de tokens y el volcado de archivo Markdown en `tests/test_cli_observability.py`.
- [x] 3.3 Implementar comandos `/doctor`, `/tree` y `/diff` en `harness/cli.py` y verificar conectividad de endpoint, árbol de archivos ignorados y diff unificado en `tests/test_cli_doctor_tree.py`.

## 4. Experiencia Visual Enriquecida con Rich y Prompt Toolkit

- [x] 4.1 Crear módulo `harness/ui.py` con componentes `rich` (paneles con bordes redondeados Unicode `╭─╮`, banners limpios, tablas de modelos y fallback seguro a texto plano) y verificar en `tests/test_ui.py`.
- [x] 4.2 Integrar `prompt_toolkit.PromptSession` con autocompletador emergente al escribir `/` en el REPL principal de `harness/cli.py` y verificar navegación de sugerencias.
- [x] 4.3 Integrar spinners compactos no bloqueantes para ejecución de herramientas y llamadas al modelo durante los turnos del agente.

## 5. Pruebas de Integración y Validación del Sistema

- [x] 5.1 Ejecutar la suite completa de pruebas unitarias (`pytest`) asegurando que todas las pruebas pasen al 100%.
- [x] 5.2 Realizar prueba de integración de punta a punta en sandbox ejecutando comandos `/help`, `/plan`, `/steps`, `/doctor`, `/tokens` y verificar salida formateada.
