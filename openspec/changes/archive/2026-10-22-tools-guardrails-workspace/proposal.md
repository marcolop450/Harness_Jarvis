# Proposal: tools-guardrails-workspace

## Why
Completar la fórmula arquitectónica del Harness dotando al agente de capacidades operativas completas: las 6 herramientas estandarizadas, una capa infranqueable de seguridad (guardrails), visibilidad del entorno de trabajo (`cwd`, `AGENT.md`) y una memoria persistente de modelos y configuraciones para reiniciar sesiones sin reconfigurar.

## What Changes
- Creación de `harness/tools.py` con las 6 herramientas estandarizadas (`read_file`, `write_file`, `edit_file`, `list_dir`, `run_command`, `search_code`), clasificación de riesgo (`AUTO` vs `CONFIRM`) y truncado estricto a 4000 caracteres.
- Creación de `harness/guardrails.py` con validación de rutas (anti-path traversal dentro del `cwd`), bloqueo total de `.env` y archivos sensibles, y confirmación interactiva obligatoria `[s/n]`.
- Módulo de persistencia local (`.harness_models.json`) que almacena la memoria de modelos agregados y el último proveedor/modelo activo para restaurarlos al reiniciar sesión.
- Comando interactivo `/model` para listar, agregar y alternar modelos en caliente.
- Soporte para ver el directorio de trabajo activo (`cwd`) e inyectar `AGENT.md` en el contexto.
- **Fuera de alcance**:
  - Servidores y protocolos MCP externos.
  - Interfaz web o GUI gráfica (se mantiene 100% en CLI / terminal).

## Capabilities

### New Capabilities
- `harness-tools`: Registro y ejecución de las 6 herramientas del sistema con esquemas JSON Schema, resiliencia ante errores y límite de 4000 caracteres.
- `security-guardrails`: Capa de seguridad preventiva para bloqueo de `.env`, restricción a `cwd` y confirmación interactiva `[s/n]`.
- `workspace-context`: Visualización y gestión del espacio de trabajo (`cwd`), lectura de instrucciones `AGENT.md`, comando `/model` y memoria persistente de modelos en `.harness_models.json`.

### Modified Capabilities
- `cli-entrypoint`: Integración de comandos `/model`, memoria persistente de modelos y despliegue del directorio activo en el prompt.
- `agent-loop`: Enrutamiento de llamadas de herramientas a través del despachador y los guardrails de confirmación.

## Impact
- Concluye los 4 módulos nucleares de `harness/`.
- Habilita la memoria persistente de modelos para sesiones recurrentes.
- Habilita la verificación aislada mediante sandbox en `tests/sandbox_tmp/`.
