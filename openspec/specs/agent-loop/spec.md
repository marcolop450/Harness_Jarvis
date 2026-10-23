# agent-loop Specification

## Purpose
Controla el ciclo de ejecución reactivo del agente mediante un bucle while con límite estricto de pasos para evitar ejecuciones descontroladas o consumo excesivo de tokens.

## Requirements

### Requirement: Ciclo de pasos acotado a MAX_STEPS
El bucle de ejecución SHALL iterar secuencialmente ejecutando pasos hasta que el modelo emita una respuesta final o se alcance el límite inamovible de MAX_STEPS igual a 15.

#### Scenario: Terminación normal por respuesta del modelo
- **GIVEN** un bucle en el paso 3 de 15
- **WHEN** el modelo genera una respuesta final sin invocar herramientas
- **THEN** el bucle termina exitosamente devolviendo el mensaje al usuario

#### Scenario: Interrupción al alcanzar MAX_STEPS
- **GIVEN** una ejecución continua que llega al paso 15 sin converger
- **WHEN** se completa el paso 15
- **THEN** el ciclo se detiene inmediatamente y emite un mensaje notificando que se alcanzó el límite de pasos

### Requirement: Registro de historial de conversación
El bucle SHALL mantener un historial de mensajes ordenado que refleje las intervenciones del usuario, respuestas del asistente y resultados de ejecución para mantener la coherencia del diálogo.

#### Scenario: Acumulación de contexto durante el ciclo
- **GIVEN** un mensaje entrante del usuario
- **WHEN** el bucle inicia la interacción
- **THEN** añade el mensaje del usuario y conserva el historial durante todos los pasos del turno

### Requirement: Despacho seguro de herramientas en el bucle
El bucle de ejecución SHALL despachar cada tool_call emitido por el modelo a través de los guardrails de seguridad antes de su ejecución e inyectar el resultado normalizado en el historial.

#### Scenario: Interceptación y ejecución de herramienta permitida
- **GIVEN** un tool_call emitido por el modelo en el paso N
- **WHEN** los guardrails validan la llamada y se ejecuta la herramienta
- **THEN** el resultado (o confirmación) se añade como mensaje de rol 'tool' y el ciclo avanza al siguiente paso

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
