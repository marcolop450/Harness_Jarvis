# Spec Delta

## ADDED Requirements

### Requirement: Autocompletado interactivo y renderizado visual enriquecido
La CLI SHALL utilizar un prompt interactivo con sugerencias flotantes al escribir '/' y renderizar paneles y cajas de texto empleando bordes Unicode redondeados y resaltado sintáctico.

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

### Requirement: Comandos de observabilidad y diagnóstico
La CLI SHALL proveer comandos '/doctor', '/tokens', '/diff', '/tree' y '/export' para auditar la salud del entorno, el consumo de contexto, las diferencias en archivos y la persistencia de la sesión.

#### Scenario: Diagnóstico integral con /doctor
- **GIVEN** una sesión activa de la CLI con configuración de modelo y servidores MCP
- **WHEN** el usuario ejecuta el comando '/doctor'
- **THEN** el sistema verifica y reporta la latencia y accesibilidad del LLM activo, junto al estado de los procesos MCP

#### Scenario: Estimación de contexto con /tokens
- **GIVEN** una conversación con turnos acumulados
- **WHEN** el usuario ejecuta '/tokens'
- **THEN** el sistema calcula y muestra el total de caracteres, la estimación de tokens y el porcentaje de uso de la ventana del modelo

#### Scenario: Inspección de cambios con /diff
- **GIVEN** una sesión donde el agente ha modificado o creado archivos
- **WHEN** el usuario ejecuta '/diff'
- **THEN** el sistema imprime en formato unificado las líneas añadidas y eliminadas de los archivos modificados

#### Scenario: Visualización del árbol de trabajo con /tree
- **GIVEN** un espacio de trabajo con directorios y archivos
- **WHEN** el usuario ejecuta '/tree'
- **THEN** el sistema imprime la jerarquía visual de archivos ignorando carpetas excluidas como .git, __pycache__ y venvs

#### Scenario: Exportación de sesión con /export
- **GIVEN** una conversación activa en memoria
- **WHEN** el usuario ejecuta '/export' o '/export <nombre_archivo>'
- **THEN** el sistema guarda el historial formateado en Markdown dentro del directorio de trabajo actual

### Requirement: Comandos de control agéntico en caliente
La CLI SHALL admitir los comandos '/plan', '/steps' y '/approval' para alterar los modos de razonamiento, límites de iteración y políticas de confirmación sin reiniciar la aplicación.

#### Scenario: Alternancia de modo con /plan
- **GIVEN** el agente en modo Actuador estándar
- **WHEN** el usuario ejecuta '/plan'
- **THEN** el sistema cambia al modo Arquitecto (solo lectura) y actualiza el prompt de la terminal para reflejar el estado activo

#### Scenario: Modificación dinámica de pasos con /steps
- **GIVEN** un límite vigente de pasos por consulta
- **WHEN** el usuario ingresa '/steps <numero>' con un valor entre 1 y 50
- **THEN** el sistema actualiza el límite de pasos del ciclo y muestra un mensaje de confirmación
