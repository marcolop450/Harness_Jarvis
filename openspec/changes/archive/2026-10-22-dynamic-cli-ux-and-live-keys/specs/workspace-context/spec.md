# Spec Delta: workspace-context

## MODIFIED Requirements

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

## ADDED Requirements

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
