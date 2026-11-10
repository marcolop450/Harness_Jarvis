# Spec Delta: workspace-context

## ADDED Requirements

### Requirement: Directiva de Verdad Fáctica (Grounded Truth) en System Prompt
El sistema SHALL inyectar en el System Prompt del espacio de trabajo una directiva obligatoria de Verdad Fáctica (Grounded Truth) que prohíbe terminantemente al modelo declarar o reportar como completadas tareas cuya herramienta de ejecución haya sido cancelada o haya fallado.

#### Scenario: Inyección de la regla de Verdad Fáctica al iniciar sesión
- **GIVEN** la construcción del system prompt para el espacio de trabajo activo
- **WHEN** se genera el contexto del entorno de ejecución
- **THEN** se incorpora la regla estricta que ordena al modelo basar todas sus conclusiones de éxito exclusivamente en la salida comprobable de las herramientas y no en sus propias suposiciones

#### Scenario: Prohibición de afirmaciones de éxito tras fallo
- **GIVEN** un modelo de lenguaje interactuando con herramientas
- **WHEN** una herramienta devuelve cancelación o error
- **THEN** la directiva de verdad fáctica constriñe al modelo a admitir que la operación no fue realizada y a solicitar instrucciones al usuario
