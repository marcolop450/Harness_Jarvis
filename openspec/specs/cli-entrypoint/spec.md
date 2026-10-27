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
La interfaz CLI SHALL reconocer comandos de barra oblicua como /model, /key, /clear, /reset y comandos de ayuda/guía (/guide, /guia, /help), mostrar el directorio de trabajo activo (cwd) y el modelo activo en un prompt dinámico, y operar de manera resiliente incluso sin claves de API ni modelos de IA configurados.

#### Scenario: Visualización del directorio de trabajo en consola
- **GIVEN** la inicialización de la terminal del agente
- **WHEN** se presenta la interfaz al usuario
- **THEN** muestra explícitamente el directorio de trabajo actual (cwd) en el encabezado inicial y en el prompt dinámico

#### Scenario: Ejecución de comando de ayuda o modelo
- **GIVEN** una sesión activa en la terminal con modelos registrados por el usuario
- **WHEN** el usuario escribe '/model' sin argumentos
- **THEN** la terminal muestra una lista limpia y numerada de los modelos registrados por el usuario, indicando proveedor, nombre del modelo y estado de autenticación

#### Scenario: Selección de modelo por índice numérico
- **GIVEN** una sesión activa en la terminal donde se listaron los modelos numerados
- **WHEN** el usuario ingresa '/model <numero>' con un índice válido (ejemplo: '/model 1')
- **THEN** el sistema actualiza el modelo activo al correspondiente, persiste la selección y muestra una confirmación visual estilizada del cambio

#### Scenario: Limpieza de pantalla de la terminal
- **GIVEN** una sesión activa con texto acumulado en la consola
- **WHEN** el usuario ingresa el comando '/clear'
- **THEN** el sistema limpia la pantalla completa de la terminal y vuelve a dibujar el encabezado limpio manteniendo el estado de la sesión intacto

#### Scenario: Activación inmediata de clave de API en memoria
- **GIVEN** una sesión interactiva en ejecución donde un proveedor carece de clave en memoria
- **WHEN** el usuario ejecuta el comando '/key <proveedor> <clave>'
- **THEN** el sistema guarda la clave en el archivo .env y la inyecta inmediatamente en os.environ del proceso activo sin requerir reinicio de la terminal

#### Scenario: Prompt dinámico contextual
- **GIVEN** una sesión activa con un directorio de trabajo y modelo seleccionados
- **WHEN** la terminal solicita la entrada del usuario
- **THEN** el texto del prompt muestra de forma compacta el nombre del directorio y el modelo activo (ejemplo: '[Pruebas | ⚡ groq:llama-3.3-70b-versatile] jarvis> ')

#### Scenario: Ejecución de guía predeterminada interactiva para nuevos usuarios
- **GIVEN** cualquier sesión de la CLI, incluso sin claves de API ni modelos configurados
- **WHEN** el usuario ejecuta el comando '/guide', '/guia' o '/help'
- **THEN** el sistema imprime una guía visual estructurada y completa explicando cómo configurar proveedores, cómo gestionar modelos y cómo dar instrucciones al agente de forma autónoma sin realizar llamadas a la red

### Requirement: Inspección y reconexión MCP
La CLI SHALL admitir /mcp y /mcp reconnect, mostrando estado, errores y herramientas habilitadas sin requerir un modelo configurado.

#### Scenario: Inspección
- **GIVEN** CLI abierta
- **WHEN** se ejecuta /mcp
- **THEN** se muestran los servidores y herramientas realmente disponibles

#### Scenario: Reconexión
- **GIVEN** servidor fallido
- **WHEN** se ejecuta /mcp reconnect
- **THEN** se reintenta su conexión y se actualiza su estado

### Requirement: MCP en ambos modos de ejecución
La CLI SHALL suministrar el mismo catálogo MCP y políticas al REPL y al modo -p.

#### Scenario: Solicitud directa
- **GIVEN** MCP configurado
- **WHEN** se inicia con -p
- **THEN** el modelo puede usar MCP y los procesos se cierran al concluir
