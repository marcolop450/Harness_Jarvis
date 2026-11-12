# Spec Delta: cli-entrypoint

## MODIFIED Requirements

### Requirement: Autocompletado interactivo y renderizado visual enriquecido
La CLI SHALL utilizar un prompt interactivo con sugerencias flotantes al escribir '/', soportar autocompletado multinivel de subcomandos y rutas de archivos locales, y renderizar paneles y cajas de texto empleando bordes Unicode redondeados y resaltado sintáctico.

#### Scenario: Despliegue de autocompletado de comandos
- **GIVEN** el usuario en la línea de comandos de la CLI
- **WHEN** escribe el caracter '/'
- **THEN** se despliega un menú flotante con los comandos disponibles y una descripción breve de cada uno

#### Scenario: Renderizado visual de paneles con bordes redondeados
- **GIVEN** una salida informativa o respuesta estructurada del sistema
- **WHEN** el sistema muestra la información en consola
- **THEN** renderiza un panel con bordes redondeados Unicode ('╭─╮') y jerarquía cromática semántica

#### Scenario: Fallback seguro en terminales no interactivas
- **GIVEN** un entorno de ejecución sin soporte para secuencias ANSI o sin TTY
- **WHEN** el sistema inicializa la interfaz
- **THEN** conmuta automáticamente a modo texto plano estándar sin caracteres de escape corruptos

#### Scenario: Autocompletado de comandos y subcomandos
- **GIVEN** el prompt de entrada interactiva de la CLI
- **WHEN** el usuario escribe '/' o '/model ' o '/approval '
- **THEN** se despliega un menú flotante desplegable con sugerencias de comandos principales y sus subcomandos específicos

#### Scenario: Autocompletado de archivos del espacio de trabajo
- **GIVEN** el usuario escribiendo una ruta o argumento que refiere a un archivo local
- **WHEN** presiona la tecla de autocompletado (Tab)
- **THEN** la CLI sugiere nombres de archivos y carpetas existentes dentro del cwd

### Requirement: Comandos de control de sesión y contexto
La interfaz CLI SHALL reconocer comandos de barra oblicua como /model, /key, /clear, /reset y comandos de ayuda/guía (/guide, /guia, /help), mostrar el directorio de trabajo activo (cwd) y el modelo activo en un prompt dinámico, y operar de manera resiliente incluso sin claves de API ni modelos de IA configurados, presentando una guía integral moderna estructurada en paneles Rich categorizados por funcionalidad.

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

#### Scenario: Despliegue de la guía moderna con paneles Rich
- **GIVEN** una sesión interactiva en la terminal
- **WHEN** el usuario escribe '/guide' o '/help'
- **THEN** la terminal renderiza paneles visuales con bordes curvos agrupando comandos de inicio, control agéntico (/plan, /approval, /steps), diagnóstico (/tree, /diff, /doctor, /tokens) y herramientas MCP
