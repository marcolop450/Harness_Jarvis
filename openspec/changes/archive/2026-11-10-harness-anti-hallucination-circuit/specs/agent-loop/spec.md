# Spec Delta: agent-loop

## MODIFIED Requirements

### Requirement: Despacho seguro de herramientas en el bucle
El bucle de ejecución SHALL despachar cada tool_call emitido por el modelo a través de los guardrails de seguridad e inyectar cualquier error operativo, de sintaxis o cancelación interactiva como respuesta fáctica de rol 'tool' para obligar al modelo a anclarse en la verdad real del entorno (Anti-Hallucination Circuit).

#### Scenario: Interceptación y ejecución de herramienta permitida
- **GIVEN** un tool_call emitido por el modelo en el paso N
- **WHEN** los guardrails validan la llamada y se ejecuta la herramienta
- **THEN** el resultado (o confirmación) se añade como mensaje de rol 'tool' y el ciclo avanza al siguiente paso

#### Scenario: Bucle de auto-reparación ante fallo de herramienta
- **GIVEN** una herramienta que falla por sintaxis, archivo no encontrado o texto no coincidente
- **WHEN** la herramienta retorna la descripción del fallo
- **THEN** el bucle inyecta el error instructivo como mensaje de rol 'tool' permitiendo al modelo autocorregir su acción en el paso siguiente

#### Scenario: Intercepción de cancelación interactiva humana (HITL)
- **GIVEN** una herramienta de escritura o consola que requiere confirmación y el usuario rechaza la operación o presiona Enter sin autorizar
- **WHEN** la herramienta retorna la cancelación
- **THEN** el bucle inyecta un mensaje explícito de cancelación con prohibición terminante de asumir la creación de archivos, impidiendo que el modelo declare el paso como completado

## ADDED Requirements

### Requirement: Anclaje Fáctico Post-Ejecución de Herramientas
El bucle de ejecución SHALL verificar el resultado reportado por las herramientas de modificación de disco y comandos de creación antes de permitir que el modelo cierre el turno como exitoso.

#### Scenario: Rechazo de afirmación falsa tras herramienta cancelada
- **GIVEN** un turno donde una herramienta de creación o comando fue denegada por el usuario
- **WHEN** el modelo emite su respuesta final de texto
- **THEN** el sistema asegura que la conversación registre el estado cancelado y no promueva estados alucinados en turnos futuros
