# workspace-context Specification

## Purpose
Proporciona visibilidad del entorno de trabajo activo (cwd, árbol de carpetas, AGENT.md), selección dinámica de modelos y memoria persistente de modelos y proveedores configurados.

## Requirements

### Requirement: Detección y visualización del espacio de trabajo
El sistema SHALL informar al usuario y al modelo el directorio de trabajo activo (cwd) y el árbol contextual del proyecto.

#### Scenario: Visualización del directorio actual
- **GIVEN** el inicio de la CLI o la invocación del comando de estado
- **WHEN** el usuario inicia la sesión
- **THEN** la interfaz muestra claramente la ruta absoluta del espacio de trabajo donde opera

### Requirement: Inyección de AGENT.md en el contexto
El sistema SHALL cargar las directrices de AGENT.md presentes en el directorio raíz del proyecto e incorporarlas en las instrucciones iniciales del sistema.

#### Scenario: Carga automática de directrices locales
- **GIVEN** un archivo AGENT.md en el directorio de trabajo
- **WHEN** se construye el prompt del sistema
- **THEN** el contenido de AGENT.md es inyectado de forma estructurada en las instrucciones

### Requirement: Comando interactivo de selección de modelo
La interfaz CLI SHALL permitir al usuario consultar y cambiar el proveedor o modelo activo dinámicamente mediante el comando /model.

#### Scenario: Cambio de modelo en caliente
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario ejecuta el comando '/model gemini gemini-2.5-flash'
- **THEN** el sistema actualiza el proveedor y modelo para las consultas subsiguientes y notifica el cambio

### Requirement: Persistencia y memoria de modelos
El sistema SHALL persistir en un archivo de configuración local (.harness_models.json) los modelos registrados por el usuario y la última configuración activa, sin incluir modelos de prueba predeterminados quemados en el sistema, permitiendo agregar y eliminar modelos explícitamente.

#### Scenario: Registro y persistencia de nuevo modelo
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario ingresa un nuevo modelo mediante el comando '/model add <proveedor> <modelo>'
- **THEN** el sistema guarda el modelo en la memoria persistente y lo marca como activo

#### Scenario: Eliminación de modelo por el usuario
- **GIVEN** un modelo registrado en el catálogo local
- **WHEN** el usuario ejecuta '/model rm <id_o_nombre>'
- **THEN** el sistema remueve el modelo del catálogo persistente y confirma la eliminación

#### Scenario: Restauración al reiniciar la sesión
- **GIVEN** una sesión previa que registró modelos o configuraciones
- **WHEN** el usuario inicia una nueva sesión de la CLI
- **THEN** el sistema recupera la lista de modelos registrados por el usuario y restaura la selección activa

### Requirement: Memoria de conversación persistente por carpeta
El sistema SHALL persistir el historial de mensajes de la sesión en un archivo de memoria dentro del espacio de trabajo (.harness_session.json) y permitir su vaciado mediante el comando /reset.

#### Scenario: Persistencia y recarga de mensajes previos
- **GIVEN** una sesión con mensajes previos en la carpeta de trabajo
- **WHEN** el usuario inicia una nueva sesión en esa misma carpeta
- **THEN** el sistema carga el historial de mensajes preservando la continuidad del contexto de trabajo

#### Scenario: Vaciado de memoria de conversación
- **GIVEN** una sesión con mensajes almacenados en la memoria de la carpeta
- **WHEN** el usuario ejecuta el comando '/reset'
- **THEN** el sistema vacía el historial de mensajes de la memoria local y confirma que la conversación ha sido reiniciada

### Requirement: Compactación inteligente del contexto (/compact)
El sistema SHALL proveer el comando '/compact' para condensar el historial de conversación actual en un resumen semántico conciso mediante el LLM activo, preservando acuerdos, decisiones de código y contexto relevante mientras reduce drásticamente el uso de tokens.

#### Scenario: Usuario ejecuta /compact con historial extenso
- **GIVEN** una sesión interactiva con múltiples turnos e historial acumulado
- **WHEN** el usuario escribe '/compact'
- **THEN** el sistema envía el historial al modelo solicitando un resumen estructurado, reemplaza los turnos anteriores por el resumen sintético consolidado y notifica la reducción lograda

#### Scenario: Ejecución de /compact con historial mínimo
- **GIVEN** una sesión recién iniciada o con menos de 2 interacciones
- **WHEN** el usuario escribe '/compact'
- **THEN** el sistema informa que el historial es demasiado breve para requerir compactación sin consumir llamadas innecesarias

### Requirement: Catálogo y listado de sesiones (/sessions)
El sistema SHALL almacenar metadatos de las sesiones ejecutadas en el espacio de trabajo y permitir listar el historial de sesiones mediante el comando '/sessions'.

#### Scenario: Listado interactivo de sesiones guardadas
- **GIVEN** sesiones previas registradas en la carpeta de sesiones del proyecto
- **WHEN** el usuario ejecuta '/sessions'
- **THEN** el sistema despliega una tabla o lista ordenada cronológicamente con ID de sesión, fecha, hora y total de mensajes

### Requirement: Reanudación de sesión histórica (/resume)
El sistema SHALL permitir reanudar una sesión previa mediante '/resume <session_id>', restaurando el historial de mensajes para continuar el diálogo.

#### Scenario: Reanudación exitosa de sesión existente
- **GIVEN** un ID de sesión válido existente en el almacenamiento local
- **WHEN** el usuario ejecuta '/resume <session_id>'
- **THEN** el sistema carga el historial correspondiente y notifica la reanudación exitosa

#### Scenario: Intento de reanudación con ID inexistente
- **GIVEN** un ID de sesión que no coincide con ningún registro previo
- **WHEN** el usuario ejecuta '/resume <id_invalido>'
- **THEN** el sistema muestra un mensaje de error claro indicando que la sesión no fue encontrada y sugiere consultar '/sessions'
