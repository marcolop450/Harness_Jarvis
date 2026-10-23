# cli-entrypoint Specification

## Purpose
Proporciona la interfaz interactiva en terminal (CLI) para iniciar el agente, capturar instrucciones del usuario y mostrar de forma limpia el progreso del bucle y las respuestas finales.

## Requirements

### Requirement: Inicio interactivo de la CLI
El sistema SHALL inicializar un entorno interactivo en la consola cuando el usuario ejecuta la aplicación, mostrando un mensaje de bienvenida y un prompt de espera.

#### Scenario: Inicio exitoso de la sesión
- **GIVEN** que el entorno tiene configurada al menos una clave de API válida
- **WHEN** el usuario ejecuta el comando de inicio en la terminal
- **THEN** el sistema muestra el banner de bienvenida y queda a la espera de la entrada del usuario

#### Scenario: Salida interactiva por el usuario
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario ingresa el comando 'exit' o 'quit'
- **THEN** el sistema termina la ejecución de manera ordenada sin errores

### Requirement: Entrada y visualización de mensajes
El sistema SHALL recibir la consulta del usuario, transferirla al bucle del agente y renderizar la respuesta generada por el modelo en la terminal.

#### Scenario: Procesamiento de consulta de usuario
- **GIVEN** el agente en estado de espera en la terminal
- **WHEN** el usuario escribe una instrucción y presiona Enter
- **THEN** el sistema envía la instrucción al bucle del agente y muestra la respuesta en pantalla

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
