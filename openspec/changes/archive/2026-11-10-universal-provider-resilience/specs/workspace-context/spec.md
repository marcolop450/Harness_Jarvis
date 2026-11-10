# Spec Delta: workspace-context

## MODIFIED Requirements

### Requirement: Detección y visualización del espacio de trabajo
El sistema SHALL informar al usuario y al modelo el directorio de trabajo activo (cwd), sanitizar comandos de entrada retirando prefijos accidentales de consola (como 'jarvis>', '>'), y garantizar que no queden activos modelos de nube sin clave válida configurada.

#### Scenario: Visualización del directorio actual
- **GIVEN** el inicio de la CLI o la invocación del comando de estado
- **WHEN** el usuario inicia la sesión
- **THEN** la interfaz muestra claramente la ruta absoluta del espacio de trabajo donde opera

#### Scenario: Sanitización de comandos pegados con prompt
- **GIVEN** el bucle interactivo de la terminal
- **WHEN** el usuario ingresa un comando con prefijo como 'jarvis> /endpoint ollama http://localhost:11434/v1'
- **THEN** el sistema remueve el prefijo 'jarvis>' y ejecuta el comando de barra oblicua /endpoint correctamente

#### Scenario: Inicio en espacio de trabajo sin clave de nube previa
- **GIVEN** una configuración global previa que apuntaba a un proveedor de nube no autenticado
- **WHEN** el usuario inicia sesión en una nueva carpeta
- **THEN** el sistema detecta la falta de clave y presenta el estado '[sin configurar]' en lugar de bloquear al usuario con advertencias
