# Tasks

## 1. Directiva y Salvaguarda Bias for Action

- [x] 1.1 Enriquecer `DEFAULT_BASE_PROMPT` en `main.py` y `build_workspace_system_prompt` en `harness/model_config.py` con la directiva estricta de acción inmediata ("Bias for Action").
- [x] 1.2 Implementar en `harness/agent_loop.py` la salvaguarda que detecta respuestas de promesa conversacional sin herramientas cuando se solicitó una modificación, reinyectando un estímulo de ejecución.
- [x] 1.3 Crear pruebas en `tests/test_agent_loop.py` validando la recuperación automática ante respuestas procrastinadoras.

## 2. Autocompletado Jerárquico y Rutas de Archivos

- [x] 2.1 Mejorar `JarvisCommandCompleter` en `harness/cli.py` para autocompletar subcomandos (`/model add`, `/model rm`, `/approval auto`, `/mcp reconnect`) y nombres de archivos de la carpeta de trabajo.
- [x] 2.2 Agregar pruebas en `tests/test_completer.py` verificando el autocompletado de subcomandos y archivos.

## 3. Renovación Visual de la Guía y Comandos de Sesión en Rich

- [x] 3.1 Implementar `print_rich_user_guide` en `harness/ui.py` con paneles categorizados y bordes curvos `╭─╮`, e integrarla en `main.py` (`/guide`, `/help`).
- [x] 3.2 Modernizar las salidas de `/sessions`, `/compact`, `/key`, `/endpoint` y `/model` en `main.py` y `harness/ui.py` para utilizar componentes Rich consistentes.

## 4. Validación y Suite de Pruebas

- [x] 4.1 Ejecutar la suite completa de pruebas (`pytest`) asegurando el 100% de tests en verde sin regresiones.
