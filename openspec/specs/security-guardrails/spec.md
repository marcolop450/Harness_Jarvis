# security-guardrails Specification

## Purpose
Implementa los mecanismos de seguridad defensivos para bloquear accesos a secretos (.env), impedir fugas de directorio (path traversal) y exigir confirmación del usuario.

## Requirements

### Requirement: Bloqueo de archivos confidenciales
El módulo guardrails SHALL interceptar y rechazar de forma inmediata cualquier intento de lectura o modificación de archivos .env y credenciales del sistema.

#### Scenario: Intento de lectura de archivo .env
- **GIVEN** una petición de herramienta para acceder a .env o .env.local
- **WHEN** los guardrails evalúan la ruta
- **THEN** la operación es bloqueada inmediatamente retornando un mensaje de violación de seguridad

### Requirement: Contención dentro del directorio de trabajo actual
El módulo guardrails SHALL validar que toda ruta destino resida estrictamente dentro del directorio de trabajo actual (cwd), impidiendo escapes mediante rutas relativas o absolutas.

#### Scenario: Intento de Path Traversal
- **GIVEN** una ruta que intenta navegar hacia carpetas superiores fuera del cwd
- **WHEN** los guardrails resuelven la ruta absoluta
- **THEN** se rechaza la ejecución y se notifica que la ruta está fuera del espacio autorizado

### Requirement: Confirmación interactiva para operaciones destructivas
Las herramientas clasificadas como CONFIRM (write_file, edit_file, run_command) SHALL solicitar aprobación interactiva mediante [s/n/a] al usuario, permitiendo autorizar individualmente, rechazar o autorizar en lote ('a') todas las acciones del turno actual para evitar confirmaciones repetitivas.

#### Scenario: Usuario autoriza la operación
- **GIVEN** una llamada a write_file o run_command pendiente de confirmación
- **WHEN** el usuario responde afirmativamente ('s', 'si', 'sí', 'ss', 'y', 'yes')
- **THEN** la herramienta procede con la ejecución de forma autorizada

#### Scenario: Usuario rechaza la operación
- **GIVEN** una llamada a run_command pendiente de confirmación
- **WHEN** el usuario responde negativamente ('n', 'no') o presiona Enter sin contenido
- **THEN** la operación es cancelada y se notifica al modelo que el usuario denegó la acción

#### Scenario: Despliegue inmediato sin retención de búfer
- **GIVEN** una operación de herramienta clasificada como CONFIRM en ejecución en Windows
- **WHEN** el sistema requiere la confirmación del usuario
- **THEN** el texto de advertencia y detalles de la acción se imprimen con volcado forzado antes de bloquear el cursor a la espera de entrada

#### Scenario: Autorización en lote para el archivo o turno activo
- **GIVEN** una operación de escritura o modificación sobre un archivo
- **WHEN** el usuario responde con la opción 'a' o 'all' (autorizar todo)
- **THEN** el sistema autoriza la operación y recuerda la aprobación para las subsiguientes modificaciones del mismo archivo durante el turno en curso sin volver a interrumpir

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
