# Propuesta: Portabilidad Global e Instalación desde Git/GitHub

## Por qué
Actualmente, si Jarvis se ejecuta en una carpeta vacía diferente a la raíz del repositorio o se instala directamente desde GitHub vía `pip install git+https://...`, los servidores MCP no inician (catálogo vacío) porque `mcp.json` solo se busca en el `workspace` local y no está empaquetado como dato del paquete. Además, la persistencia de claves y modelos requiere configuración repetitiva en cada carpeta nueva.

## Qué Cambiará
- **Configuración en Cascada Global/Local para MCP:** Jarvis buscará `mcp.json` primero en el `workspace` activo; si no existe, recurrirá a `~/.harness/mcp.json` o a la plantilla base empaquetada.
- **Empaquetado Completo para Instalación desde Git:** Se incluirá la plantilla `mcp.json` dentro de los datos del paquete en `pyproject.toml` (`package_data`) para garantizar que instalaciones remotas (`pip install git+...`) cuenten con los recursos necesarios.
- **Directorio de Usuario Global (`~/.harness/`):** Almacenamiento centralizado de claves API (`~/.harness/.env`), catálogo de modelos y plantillas MCP, evitando reconfiguración en cada carpeta virgen.
- **Auto-inicialización Transparente:** Si el usuario ejecuta `jarvis` en cualquier carpeta sin configuración previa, el arnés inicializa automáticamente el entorno global con los servidores MCP predeterminados (`fetch` y `git`).

## Capacidades

### Nuevas Capacidades
*(Ninguna nueva capacidad duradera; se refinan capacidades existentes).*

### Capacidades Modificadas
- `mcp-integration`: Añade resolución en cascada de `mcp.json` (Workspace -> Global `~/.harness/` -> Empaquetado) y auto-inicialización en carpetas vírgenes.
- `cli-distribution`: Añade empaquetado formal de datos no-código (`package_data`), garantizando portabilidad al instalar desde Git/GitHub.
- `workspace-context`: Centraliza la memoria de modelos y claves de API en el directorio de usuario (`~/.harness/`) con precedencia de `.env` local.

## Impacto
- **Archivos afectados:** `pyproject.toml`, `harness/mcp_client.py`, `harness/model_config.py`, `main.py`.
- **Compatibilidad:** 100% retrocompatible. Si un proyecto ya tiene su propio `mcp.json` o `.env` local, este tiene prioridad sobre la configuración global.
- **Fuera de alcance:** No se agregan nuevos servidores MCP de terceros ni se modifican los guardrails de seguridad.
