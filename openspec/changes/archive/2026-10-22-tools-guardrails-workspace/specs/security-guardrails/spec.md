# Spec Delta: security-guardrails

## Purpose

Implementa los mecanismos de seguridad defensivos para bloquear accesos a secretos (.env), impedir fugas de directorio (path traversal) y exigir confirmación del usuario.

## ADDED Requirements

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
Las herramientas clasificadas como CONFIRM (write_file, edit_file, run_command) SHALL solicitar aprobación interactiva [s/n] al usuario antes de ejecutarse.

#### Scenario: Usuario autoriza la operación
- **GIVEN** una llamada a write_file pendiente de confirmación
- **WHEN** el usuario responde afirmativamente ('s' o 'y')
- **THEN** la herramienta procede con la modificación

#### Scenario: Usuario rechaza la operación
- **GIVEN** una llamada a run_command pendiente de confirmación
- **WHEN** el usuario responde negativamente ('n')
- **THEN** la operación es cancelada y se notifica al modelo que el usuario denegó la acción
