# cli-entrypoint Specification

## Purpose
Proporciona la interfaz interactiva en terminal (CLI) para iniciar el agente, capturar instrucciones del usuario y mostrar de forma limpia el progreso del bucle y las respuestas finales.

## Requirements

### Requirement: Inicio interactivo de la CLI
El sistema SHALL inicializar un entorno interactivo en la consola cuando el usuario ejecuta la aplicación, reflejando el estado de configuración de proveedores y modelos de forma transparente.

#### Scenario: Inicio exitoso de la sesión
- **GIVEN** que el entorno tiene configurada al menos una clave de API válida o modelo seleccionado
- **WHEN** el usuario ejecuta el comando de inicio en la terminal
- **THEN** el sistema muestra el banner de bienvenida con el modelo activo y queda a la espera de la entrada del usuario.

#### Scenario: Inicio sin configuración de proveedor o modelo
- **GIVEN** un entorno recién instalado sin memoria de modelos ni claves de API
- **WHEN** el usuario inicia la CLI
- **THEN** el banner muestra '[SIN CONFIGURAR]' en proveedor y modelo con estado pendiente, manteniendo el REPL abierto para aceptar comandos.

#### Scenario: Intento de consulta sin proveedor configurado
- **GIVEN** una sesión interactiva sin proveedor ni modelo configurado
- **WHEN** el usuario ingresa una consulta de texto
- **THEN** el sistema muestra un mensaje de orientación indicando cómo configurar un proveedor usando /key o /model sin realizar llamadas de red fallidas.

#### Scenario: Salida interactiva por el usuario
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario ingresa el comando 'exit' o 'quit'
- **THEN** el sistema termina la ejecución de manera ordenada sin errores.

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
