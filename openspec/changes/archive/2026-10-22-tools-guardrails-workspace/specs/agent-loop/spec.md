# Spec Delta: agent-loop

## ADDED Requirements

### Requirement: Despacho seguro de herramientas en el bucle
El bucle de ejecución SHALL despachar cada tool_call emitido por el modelo a través de los guardrails de seguridad antes de su ejecución e inyectar el resultado normalizado en el historial.

#### Scenario: Interceptación y ejecución de herramienta permitida
- **GIVEN** un tool_call emitido por el modelo en el paso N
- **WHEN** los guardrails validan la llamada y se ejecuta la herramienta
- **THEN** el resultado (o confirmación) se añade como mensaje de rol 'tool' y el ciclo avanza al siguiente paso
