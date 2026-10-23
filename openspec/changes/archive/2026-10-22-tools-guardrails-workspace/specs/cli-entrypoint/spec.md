# Spec Delta: cli-entrypoint

## ADDED Requirements

### Requirement: Comandos de control de sesión y contexto
La interfaz CLI SHALL reconocer comandos de barra oblicua como /model y mostrar el directorio de trabajo activo (cwd) en el banner o prompt de la terminal.

#### Scenario: Visualización del directorio de trabajo en consola
- **GIVEN** la inicialización de la terminal del agente
- **WHEN** se presenta la interfaz al usuario
- **THEN** muestra explícitamente el directorio de trabajo actual (cwd)

#### Scenario: Ejecución de comando de ayuda o modelo
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario escribe '/model' sin argumentos
- **THEN** la terminal muestra el proveedor y modelo en uso junto con las alternativas disponibles
