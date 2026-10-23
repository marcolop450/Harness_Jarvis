# Tasks: tools-guardrails-workspace

## 1. Guardrails de Seguridad (`harness/guardrails.py`)

- [x] 1.1 Implementar validación de rutas seguras dentro de `cwd` (anti-path traversal) y bloqueo estricto de `.env` y archivos confidenciales en `harness/guardrails.py`, verificando con tests unitarios.
- [x] 1.2 Implementar el mecanismo de confirmación interactiva `[s/n]` para operaciones de riesgo `CONFIRM` con soporte para cancelación, verificando con tests simulados.

## 2. Herramientas del Agente (`harness/tools.py`)

- [x] 2.1 Definir las especificaciones JSON Schema y matriz de riesgo (`AUTO` vs `CONFIRM`) para las 6 herramientas (`read_file`, `write_file`, `edit_file`, `list_dir`, `run_command`, `search_code`), verificando su esquema con tests.
- [x] 2.2 Implementar la función de truncado a 4000 caracteres y las 3 herramientas de lectura (`read_file`, `list_dir`, `search_code`), verificando su ejecución con tests unitarios.
- [x] 2.3 Implementar las 3 herramientas de modificación (`write_file`, `edit_file`, `run_command`) conectadas con los guardrails, verificando su comportamiento en entorno sandbox.
- [x] 2.4 Implementar el despachador unificado `execute_tool(name, arguments)` con captura resiliente de excepciones, verificando el retorno de errores explicativos al LLM.

## 3. Conexión del Bucle, Memoria de Modelos y Contexto del Workspace

- [x] 3.1 Implementar la persistencia de memoria de modelos en `.harness_models.json` (guardar modelos agregados y restaurar última selección activa al reiniciar sesión), verificando con tests unitarios.
- [x] 3.2 Integrar el catálogo y despachador de herramientas en `harness/agent_loop.py` para procesar llamadas reales durante el ciclo `while`, verificando con tests simulados.
- [x] 3.3 Implementar la detección del espacio de trabajo (`cwd`, estructura básica e inyección de `AGENT.md` si existe) en el contexto inicial del agente, verificando la construcción del prompt.
- [x] 3.4 Extender `main.py` mostrando el directorio de trabajo activo (`cwd`), conectando la memoria persistente y soportando el comando interactivo `/model` para listar, agregar y alternar modelos en caliente, verificando con tests de CLI.

## 4. Verificación de Seguridad en Sandbox (`tests/sandbox_tmp/`)

- [x] 4.1 Implementar y ejecutar la suite integral de sandbox en `tests/test_sandbox.py` verificando edición correcta, bloqueo estricto ante `.env`, bloqueo de path traversal y cancelación interactiva.
