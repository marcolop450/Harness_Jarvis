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
El bucle SHALL mantener un historial de mensajes ordenado e inyectar proactivamente el contexto del entorno (SO, CWD, Git, JARVIS.md) en el System Prompt, aplicando Observation Masking sobre una copia efímera para ahorrar tokens de contexto.

#### Scenario: Acumulación de contexto durante el ciclo
- **GIVEN** un mensaje entrante del usuario
- **WHEN** el bucle inicia la interacción
- **THEN** añade el mensaje del usuario y conserva el historial durante todos los pasos del turno

#### Scenario: Inyección proactiva de contexto de entorno
- **GIVEN** el inicio de un turno en el bucle del agente
- **WHEN** se construye el prompt del sistema
- **THEN** se inyectan automáticamente el SO, la ruta CWD, la lista superficial de archivos, el estado de Git y las reglas de JARVIS.md o AGENT.md

#### Scenario: Enmascaramiento de observaciones remotas (Observation Masking)
- **GIVEN** una conversación con llamadas a herramientas anteriores a los últimos 4 pasos
- **WHEN** se prepara el payload para el modelo de lenguaje
- **THEN** se genera una copia efímera donde las salidas antiguas extensas se reemplazan por resúmenes breves sin alterar el historial persistente en memoria

### Requirement: Despacho seguro de herramientas en el bucle
El bucle de ejecución SHALL despachar cada tool_call emitido por el modelo a través de los guardrails de seguridad e inyectar cualquier error operativo o de sintaxis como respuesta de rol 'tool' para permitir su auto-reparación (Self-Healing).

#### Scenario: Interceptación y ejecución de herramienta permitida
- **GIVEN** un tool_call emitido por el modelo en el paso N
- **WHEN** los guardrails validan la llamada y se ejecuta la herramienta
- **THEN** el resultado (o confirmación) se añade como mensaje de rol 'tool' y el ciclo avanza al siguiente paso

#### Scenario: Bucle de auto-reparación ante fallo de herramienta
- **GIVEN** una herramienta que falla por sintaxis, archivo no encontrado o texto no coincidente
- **WHEN** la herramienta retorna la descripción del fallo
- **THEN** el bucle inyecta el error instructivo como mensaje de rol 'tool' permitiendo al modelo autocorregir su acción en el paso siguiente

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
