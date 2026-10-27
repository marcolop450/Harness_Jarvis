## Why
Las funciones actuales etiquetadas MCP ejecutan bibliotecas locales y no conectan con servidores MCP. Jarvis necesita tres integraciones verificables y una explicación técnica fiel para la defensa.

## What Changes
- Cliente MCP persistente por stdio, descubrimiento y llamadas reales a Fetch, Git y Filesystem.
- Configuración portable, versiones fijadas, permisos locales y comandos /mcp y /mcp reconnect.
- **BREAKING**: retirar mcp_fetch y mcp_git_info locales; renombrar mcp_sqlite_query a sqlite_query y confirmar escrituras.
- Corregir reglas de arquitectura obsoletas y documentar instalación, pruebas y límites.

## Capabilities
### New Capabilities
- `mcp-integration`: conexiones, configuración, descubrimiento, ejecución y cierre de servidores MCP.
### Modified Capabilities
- `harness-tools`: catálogo mixto nativo/MCP, nombres y truncado estricto.
- `cli-entrypoint`: estado, reconexión e integración en ambos modos.
- `security-guardrails`: políticas para red, archivos, Git y SQLite.

## Impact
SDK MCP y servidores Python y Node fijados; gestor de conexiones independiente del adaptador LLM. Artefactos y documentación en español; commits con identidad Git existente, sin coautorías ni push. Fuera de alcance: integrar subagentes, reparar compactación, añadir interfaz web o aislar completamente comandos de consola.
