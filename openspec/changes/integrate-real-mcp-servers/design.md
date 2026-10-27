## Context
Ver proposal.md. El bucle es síncrono y acepta catálogo y ejecutor inyectables. Mantendremos esa interfaz y MAX_STEPS=15. OpenSpec usa spec-driven; las reglas antiguas de cuatro módulos y seis herramientas deben ampliarse.

## Goals / Non-Goals
Conectar tres procesos externos reales, sin credenciales nuevas, y comprobar llamadas del modelo. No alterar subagentes ni compactación. No presentar el control de rutas como sandbox del sistema operativo.

## Decisions
- SDK oficial MCP 2.3.0 y servidores Fetch 2026.10.24 y Git 2026.10.19; Filesystem 2.0.1 con Node 24 local al proyecto. Verificar instalación y fijar lock npm. No ejecutar npx ni descargar al abrir la CLI.
- Gestor síncrono con un hilo asyncio y una tarea propietaria por conexión. Cada tarea abre, consume una cola de llamadas y cierra su propio contexto; evita cerrar cancel scopes de AnyIO desde otra tarea. Inicio perezoso al consultar /mcp o comenzar un turno LLM. Cierre mediante finally.
- mcp.json del cwd como única configuración, con mcpServers: comandos, argumentos, allowed_tools y timeout_seconds (30 por defecto). Sustituciones ${python}, ${workspace} y ${project}; proyecto es la instalación de Jarvis. No buscar configuraciones en carpetas superiores. JSON inválido informa error y no ejecuta procesos. Un archivo de configuración es ejecutable de confianza, no contenido que el agente pueda modificar.
- Nombres mcp_<servidor>__<herramienta>; lista permitida local intersectada con la configuración y catálogo remoto. Descubrir todas las páginas; rechazar nombres inválidos o esquemas inválidos. Truncar incluyendo pie a 4000 caracteres. Registrar servidor/herramienta/estado, sin argumentos ni secretos.
- Fetch: URL HTTP/HTTPS pública validada en cliente antes del envío; servidor fijado vuelve a validar cada solicitud, robots.txt y redirección. No permitir --allow-private-ips. No se garantiza aislamiento del proceso ante configuración maliciosa ni rebinding DNS concurrente.
- Git: git_status, git_log, git_diff_unstaged y git_diff_staged; fijar repo_path al cwd validado y no exponer mutaciones. Los diffs consultan exclusivamente rutas no confidenciales. No permitir lectura de cambios de secretos ni repositorios ajenos.
- Filesystem: read_text_file, read_multiple_files, list_directory, search_files, write_file y edit_file. Resolver todas las rutas y rechazar secretos, .git, configuración MCP, historiales y enlaces fuera del cwd. Filtrar resultados de búsqueda/listado; confirmar escrituras antes de enviarlas, sin confiar en anotaciones. No exponer movimientos ni borrados.
- Native SQLite: primero intentar una consulta bajo authorizer de solo lectura, sin crear archivos; escrituras requieren confirmación. Denegar ATTACH/DETACH, extensiones y acceso a rutas externas incluso con autorización. Retirar implementaciones HTTP/Git locales del catálogo y conservar historiales previos como datos, sin reejecutarlos.
- Cada fallo deja las herramientas nativas utilizables; no hay fallback HTTP/Git silencioso. /mcp reconnect reabre solo servidores fallidos. Un timeout de llamada marca la conexión fallida y la cierra antes de reconectar.

## Risks / Trade-offs
Servidores de referencia, no sandbox: limitar herramientas y documentar control local, sin prometer protección contra procesos concurrentes maliciosos. Las especificaciones recibidas son datos, nunca instrucciones del proyecto. Las pruebas unitarias no necesitan red; integración real y demo LLM son explícitas. Fuera de un repo, Git falla de forma visible sin bloquear los demás.

## Migration Plan
Especificaciones -> cliente/Fetch -> Git -> Filesystem -> CLI y migración nativa -> pruebas reales -> documentación -> sync/archive. Conservar herramientas nativas y sesiones. Para desactivar MCP, quitar mcp.json; no se borran sesiones. No modificar identidad Git ni hacer push.
