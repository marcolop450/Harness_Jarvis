## ADDED Requirements

### Requirement: Políticas MCP locales obligatorias
Jarvis SHALL autorizar herramientas y validar argumentos localmente sin confiar en anotaciones remotas; Git solo permite lectura del repositorio activo y Filesystem solo rutas autorizadas sin secretos.

#### Scenario: Ruta prohibida
- **GIVEN** ruta externa, secreto o enlace que sale del cwd
- **WHEN** se solicita lectura o escritura MCP
- **THEN** se rechaza antes de enviar, incluidas listas de rutas

#### Scenario: Escritura confirmada o rechazada
- **GIVEN** escritura válida pendiente
- **WHEN** el usuario autoriza o rechaza
- **THEN** solo la autorización permite ejecutar; el rechazo no modifica archivos

#### Scenario: Git y herramientas desconocidas
- **GIVEN** herramienta no habilitada o repositorio ajeno
- **WHEN** se intenta invocar
- **THEN** se rechaza sin envío al servidor

### Requirement: Fetch limitado a destinos públicos
Fetch SHALL rechazar protocolos distintos de HTTP/HTTPS y direcciones no públicas, incluyendo redirecciones y robots.txt.

#### Scenario: URL privada
- **GIVEN** URL local, privada o resolución DNS no pública
- **WHEN** se intenta consultar
- **THEN** se rechaza sin recuperar contenido privado

#### Scenario: Redirección privada
- **GIVEN** URL pública que redirige a red privada
- **WHEN** el servidor procesa el salto
- **THEN** bloquea la solicitud al destino privado

### Requirement: SQLite nativo con escrituras autorizadas
sqlite_query SHALL confirmar escrituras y bloquear anexión de bases, carga de extensiones y rutas fuera del espacio de trabajo.

#### Scenario: Consulta
- **GIVEN** base existente
- **WHEN** se ejecuta SELECT
- **THEN** devuelve resultados sin modificar ni pedir confirmación

#### Scenario: Mutación
- **GIVEN** sentencia de escritura
- **WHEN** no se autoriza
- **THEN** no crea ni modifica la base

#### Scenario: Escape SQL
- **GIVEN** sentencia ATTACH o carga de extensión
- **WHEN** se intenta ejecutar aun con autorización
- **THEN** se deniega el acceso
