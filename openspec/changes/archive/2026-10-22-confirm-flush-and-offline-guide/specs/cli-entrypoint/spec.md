# Spec Delta: cli-entrypoint

## MODIFIED Requirements

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
