# Design: tools-guardrails-workspace

## Context

Habiendo implementado el núcleo de conexión multi-API y el bucle de razonamiento acotado, el agente requiere ahora interactuar con el entorno de forma segura, productiva y con memoria de sesión para recordar modelos configurados.

## Goals / Non-Goals

**Goals:**
- Implementar `harness/tools.py` con las 6 herramientas estandarizadas (`read_file`, `write_file`, `edit_file`, `list_dir`, `run_command`, `search_code`) bajo esquemas JSON Schema y truncado estricto a 4000 caracteres.
- Implementar `harness/guardrails.py` con validación estricta de rutas dentro del `cwd`, bloqueo de archivos `.env*` y confirmación interactiva `[s/n]` para herramientas de riesgo `CONFIRM`.
- Implementar la memoria persistente de modelos (`.harness_models.json`) que almacene los modelos registrados y restaure el último activo al reabrir la sesión.
- Proveer visibilidad del espacio de trabajo (mostrar `cwd` en banner/prompt) e inyectar `AGENT.md` si existe en el directorio raíz.
- Implementar el comando `/model` en `main.py` para listar, agregar y alternar proveedores y modelos en caliente.
- Crear una suite de verificación en sandbox temporal (`tests/sandbox_tmp/`).

**Non-Goals:**
- Implementar integración con servidores MCP remotos.
- Soporte para entornos multi-usuario concurrentes.

## Decisions

### Decisión 1: Matriz de Riesgo y Despachador de Herramientas
- **Elección**: Categorizar cada herramienta con un enum `RiskLevel`:
  - `AUTO`: `read_file`, `list_dir`, `search_code` (ejecución sin fricción tras pasar guardrails de lectura).
  - `CONFIRM`: `write_file`, `edit_file`, `run_command` (requieren confirmación interactiva `[s/n]`).
- **Razón**: Equilibra la autonomía del agente al explorar el proyecto con la máxima seguridad del usuario ante escrituras o ejecuciones arbitrarias.

### Decisión 2: Pipeline de Guardrails en Tres Pasos
- **Elección**: Toda operación de herramienta que reciba una ruta pasa secuencialmente por:
  1. `validate_safe_path(path)`: Resuelve la ruta canónica y verifica `path.is_relative_to(cwd)`.
  2. `check_sensitive_file(path)`: Bloquea `.env`, `.env.*`, claves privadas y ficheros críticos.
  3. `confirm_execution(tool_name, arguments)`: Si el riesgo es `CONFIRM`, solicita `[s/n]` interactivo.
- **Razón**: Garantiza defensa en profundidad e imposibilita fugas de datos o desbordamiento de directorio.

### Decisión 3: Memoria Persistente de Modelos (`.harness_models.json`)
- **Elección**: Guardar en `.harness_models.json` un diccionario con `active_provider`, `active_model` y la lista de modelos conocidos por proveedor:
  - Inicia con una lista base predeterminada y permite que el usuario agregue modelos libres con `/model <prov> <modelo>`.
  - Al iniciar `main.py`, se lee este archivo para restaurar la sesión automáticamente.
- **Razón**: Evita tener que reescribir nombres de modelos cada vez que se reinicia la terminal.

### Decisión 4: Truncado Estricto Centralizado (4000 Caracteres)
- **Elección**: Una función envolvente `truncate_output(text: str, max_chars: int = 4000)` que recorta al carácter 4000 y agrega una nota clara sobre el truncado.
- **Razón**: Protege la ventana de contexto de los modelos y evita consumo excesivo de tokens al leer ficheros grandes o salidas de consola.

### Decisión 5: Comando `/model` y Conciencia de Contexto en `main.py`
- **Elección**: Manejar comandos especiales que comiencen con `/` directamente en el bucle REPL de `main.py`:
  - `/model`: Muestra el proveedor y modelo activo y la lista de modelos guardados en la memoria.
  - `/model <proveedor> <modelo>`: Cambia dinámicamente el modelo y lo guarda en la memoria persistente.
  - Inyección en el prompt de sistema del `cwd` actual y del contenido de `AGENT.md` (si existe).

## Risks / Trade-offs

- **Riesgo**: Bloqueo de comandos interactivos prolongados en `run_command`.
  - **Mitigación**: Timeout explícito por defecto de 30 segundos en `subprocess.run`.
- **Riesgo**: Corrupción o borrado accidental de `.harness_models.json`.
  - **Mitigación**: Carga defensiva con `try/except` que se regenera con valores predeterminados seguros si el archivo se daña.
