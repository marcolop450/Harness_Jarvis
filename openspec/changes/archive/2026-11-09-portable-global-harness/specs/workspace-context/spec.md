# Spec Delta: workspace-context

## MODIFIED Requirements

### Requirement: Persistencia y memoria de modelos
El sistema SHALL persistir en un archivo de configuración local o en el directorio global del usuario (`~/.harness/models.json`) los modelos registrados y la selección activa, con precedencia de la configuración del workspace local si está presente.

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

#### Scenario: Precedencia de configuración en cascada
- **GIVEN** un entorno con configuración global en `~/.harness/` y configuración local en el workspace
- **WHEN** se inicia Jarvis en ese workspace
- **THEN** la configuración local tiene precedencia sobre la global para esa sesión
