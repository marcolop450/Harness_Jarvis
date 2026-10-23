# Spec Delta: workspace-context

## Purpose

Proporciona visibilidad del entorno de trabajo activo (cwd, árbol de carpetas, AGENT.md), selección dinámica de modelos y memoria persistente de modelos y proveedores configurados.

## ADDED Requirements

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
El sistema SHALL persistir en un archivo de configuración local (.harness_models.json) los modelos registrados y la última configuración activa, recargándolos automáticamente al reiniciar sesión.

#### Scenario: Registro y persistencia de nuevo modelo
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario ingresa un nuevo modelo mediante el comando /model
- **THEN** el sistema guarda el modelo en la memoria persistente y lo marca como activo

#### Scenario: Restauración al reiniciar la sesión
- **GIVEN** una sesión previa que registró modelos o configuraciones
- **WHEN** el usuario inicia una nueva sesión de la CLI
- **THEN** el sistema recupera la lista de modelos recordados y restaura la selección activa
