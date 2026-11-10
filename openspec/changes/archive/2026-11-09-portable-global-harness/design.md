# Diseño Técnico: Portabilidad Global e Instalación desde Git

## Contexto
Actualmente Jarvis resuelve rutas de configuración (`mcp.json`, `.harness_models.json`) relativas al directorio de trabajo actual (`workspace = cwd`). Al ejecutar el comando en una carpeta nueva sin estos archivos o instalarlo en un entorno remoto vía `pip install git+...`, el catálogo MCP queda vacío y se pierden las configuraciones globales del usuario.

## Metas / No Metas

**Metas:**
- Permitir que Jarvis se instale desde un repositorio Git remoto (`pip install git+https://...`) y funcione de inmediato en cualquier carpeta del sistema operativo.
- Implementar resolución de configuración en cascada: `Workspace Local` -> `Directorio de Usuario Global (~/.harness/)` -> `Plantilla Empaquetada`.
- Asegurar que la sustitución de `${workspace}` en servidores MCP como `git` apunte dinámicamente al CWD de la sesión activa, incluso usando la configuración global.
- Permitir persistencia global de claves de API en `~/.harness/.env` con precedencia de `.env` local si existe.

**No Metas:**
- No modificar el esquema JSON de los servidores MCP ni sus herramientas permitidas.
- No alterar las políticas de seguridad ni la gobernanza Smart HITL en `guardrails.py`.

## Decisiones Técnicas

### 1. Directorio Global del Usuario (`~/.harness/`)
- **Ubicación:** `Path.home() / ".harness"` (en Windows: `C:\Users\<Usuario>\.harness`).
- **Archivos:**
  - `mcp.json`: Servidores globales compartidos (`fetch`, `git`).
  - `config.json` o `models.json`: Catálogo de modelos del usuario y selección activa persistente.
  - `.env`: Claves de API globales para no tener que reingresarlas en cada carpeta nueva.
- **Alternativas consideradas:** Guardar en AppData o variables de registro de Windows. Se descartó en favor de `~/.harness/` por ser el estándar multiplataforma universal seguido por herramientas como Git (`~/.gitconfig`), Docker (`~/.docker`) y Claude Code.

### 2. Plantilla Base Empaquetada y `package_data`
- **Ubicación:** `harness/data/default_mcp.json`.
- **Acceso:** Vía `importlib.resources` o ruta relativa a `harness/`.
- **Configuración en `pyproject.toml`:**
  ```toml
  [tool.setuptools.package-data]
  harness = ["data/*.json"]
  ```
  Esto garantiza que al ejecutar `pip install git+...`, setuptools copie los archivos JSON a `site-packages`.

### 3. Cascada de Carga de MCP (`load_config`)
- Si `workspace / "mcp.json"` existe y es válido, se usa ese archivo (prioridad local).
- Si no, se evalúa `Path.home() / ".harness" / "mcp.json"`.
- Si `~/.harness/mcp.json` no existe, se crea automáticamente copiando la plantilla empaquetada.
- Al expandir variables, `${workspace}` se resuelve siempre al `workspace` activo de la sesión (CWD), garantizando que `mcp_server_git` inspeccione el repositorio de la carpeta donde el usuario abrió Jarvis.

### 4. Cascada de Carga de Variables de Entorno (`.env`)
- Se ejecuta `load_dotenv(Path.home() / ".harness" / ".env")` primero (claves base del usuario).
- Luego se ejecuta `load_dotenv(workspace / ".env", override=True)` (el proyecto local tiene precedencia y puede sobreescribir claves).

## Riesgos y Mitigaciones
- **[Riesgo]:** Conflictos si el usuario modifica `~/.harness/mcp.json` con sintaxis errónea.
  → **Mitigación:** Captura de excepciones con *graceful degradation*; si el JSON global falla, emite warning y utiliza las herramientas nativas sin caerse.
- **[Riesgo]:** En entornos CI o contenedores donde `~` no tiene permisos de escritura.
  → **Mitigación:** Detección de fallos en creación de `~/.harness/` con fallback en memoria a la plantilla empaquetada en modo solo lectura.
