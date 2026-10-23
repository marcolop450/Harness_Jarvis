# Spec Delta: workspace-context

## ADDED Requirements

### Requirement: Compactación inteligente del contexto (/compact)
El sistema SHALL proveer el comando '/compact' para condensar el historial de conversación actual en un resumen semántico conciso mediante el LLM activo, preservando acuerdos, decisiones de código y contexto relevante mientras reduce drásticamente el uso de tokens.

#### Scenario: Usuario ejecuta /compact con historial extenso
- **GIVEN** una sesión interactiva con múltiples turnos e historial acumulado
- **WHEN** el usuario escribe '/compact'
- **THEN** el sistema envía el historial al modelo solicitando un resumen estructurado, reemplaza los turnos anteriores por el resumen sintético consolidado y notifica la reducción lograda

#### Scenario: Ejecución de /compact con historial mínimo
- **GIVEN** una sesión recién iniciada o con menos de 2 interacciones
- **WHEN** el usuario escribe '/compact'
- **THEN** el sistema informa que el historial es demasiado breve para requerir compactación sin consumir llamadas innecesarias

### Requirement: Catálogo y listado de sesiones (/sessions)
El sistema SHALL almacenar metadatos de las sesiones ejecutadas en el espacio de trabajo y permitir listar el historial de sesiones mediante el comando '/sessions'.

#### Scenario: Listado interactivo de sesiones guardadas
- **GIVEN** sesiones previas registradas en la carpeta de sesiones del proyecto
- **WHEN** el usuario ejecuta '/sessions'
- **THEN** el sistema despliega una tabla o lista ordenada cronológicamente con ID de sesión, fecha, hora y total de mensajes

### Requirement: Reanudación de sesión histórica (/resume)
El sistema SHALL permitir reanudar una sesión previa mediante '/resume <session_id>', restaurando el historial de mensajes para continuar el diálogo.

#### Scenario: Reanudación exitosa de sesión existente
- **GIVEN** un ID de sesión válido existente en el almacenamiento local
- **WHEN** el usuario ejecuta '/resume <session_id>'
- **THEN** el sistema carga el historial correspondiente y notifica la reanudación exitosa

#### Scenario: Intento de reanudación con ID inexistente
- **GIVEN** un ID de sesión que no coincide con ningún registro previo
- **WHEN** el usuario ejecuta '/resume <id_invalido>'
- **THEN** el sistema muestra un mensaje de error claro indicando que la sesión no fue encontrada y sugiere consultar '/sessions'
