# Spec Delta: security-guardrails

## MODIFIED Requirements

### Requirement: Confirmación interactiva para operaciones destructivas
Las herramientas clasificadas como Nivel 1 (escrituras) o Nivel 2 (comandos fuera de whitelist) SHALL solicitar aprobación interactiva mediante [s/n/a] al usuario, permitiendo autorizar individualmente, rechazar o autorizar en lote ('a') el archivo durante toda la sesión activa, ejecutando automáticamente comandos seguros sin operadores de encadenamiento.

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

#### Scenario: Autorización persistente durante toda la sesión activa
- **GIVEN** un archivo autorizado previamente con la opción 'a'
- **WHEN** el modelo ejecuta nuevas escrituras sobre el mismo archivo en turnos posteriores de la misma sesión
- **THEN** el sistema autoriza la operación automáticamente sin volver a interrumpir al usuario

#### Scenario: Ejecución automática de comandos seguros en whitelist sin encadenamiento
- **GIVEN** un comando de consola que coincide con un prefijo seguro (pytest, git diff, ruff) y no contiene operadores de shell (&&, ;, |, >, <)
- **WHEN** se evalúa el comando en los guardrails
- **THEN** se clasifica como seguro y se ejecuta sin solicitar confirmación interactiva
