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
Las herramientas clasificadas como CONFIRM (write_file, edit_file, run_command) SHALL desplegar de forma inmediata en la pantalla el mensaje de advertencia con volcado explícito de búfer y solicitar aprobación interactiva [s/n] al usuario evaluando con tolerancia variantes afirmativas comunes.

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
