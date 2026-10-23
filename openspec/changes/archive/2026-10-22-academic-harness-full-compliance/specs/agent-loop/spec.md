# Spec Delta: agent-loop

## ADDED Requirements

### Requirement: Medición y reporte del tiempo de respuesta
El bucle de ejecución SHALL cronometrar la duración de cada turno completo del agente y reportar el tiempo transcurrido en segundos o milisegundos junto a la respuesta final.

#### Scenario: Visualización del tiempo de ejecución en turno completado
- **GIVEN** un turno interactivo del usuario
- **WHEN** el ciclo de agente completa la respuesta final
- **THEN** se imprime una línea informativa indicando el tiempo transcurrido (e.g., '[⏱️ 2.34s]')

### Requirement: Subagente especializado con contexto aislado
El sistema SHALL proveer la capacidad de ejecutar un subagente de investigación aislado que recibe una tarea específica con un contexto limpio y devuelve un resumen conciso al orquestador principal, evitando contaminar la ventana de tokens del contexto padre.

#### Scenario: Ejecución de subagente para exploración de archivos
- **GIVEN** una instrucción compleja o comando que requiere investigación detallada
- **WHEN** se invoca el subagente de investigación
- **THEN** el subagente ejecuta en su propio contexto independiente con herramientas de solo lectura y retorna exclusivamente un sumario ejecutivo al bucle principal
