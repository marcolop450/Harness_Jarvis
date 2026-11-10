# Spec Delta: agent-loop

## MODIFIED Requirements

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
