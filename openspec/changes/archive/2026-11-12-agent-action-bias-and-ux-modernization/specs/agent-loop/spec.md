# Spec Delta: agent-loop

## ADDED Requirements

### Requirement: Directiva y Salvaguarda de Acción Inmediata (Bias for Action)
El bucle de ejecución SHALL exigir la invocación inmediata de herramientas de acción ante solicitudes de creación, modificación o inspección de archivos, detectando cuando un modelo emite promesas conversacionales vacías sin llamadas a herramientas e induciendo su ejecución.

#### Scenario: Detección y corrección de promesa conversacional sin herramientas
- **GIVEN** un turno donde el usuario solicitó crear, editar o mejorar un archivo de código
- **WHEN** el modelo genera únicamente una respuesta textual de promesa como 'Entendido, voy a modificar el archivo' sin emitir ningún tool_call
- **THEN** el bucle de ejecución intercepta la omisión, inyecta un aviso correctivo exigiendo la ejecución inmediata de la herramienta y continúa el turno para aplicar los cambios reales en disco
