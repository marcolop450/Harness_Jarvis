# Spec Delta: mcp-integration

## MODIFIED Requirements

### Requirement: Conexiones MCP reales y configuración portable
Jarvis SHALL conectar Fetch y Git mediante servidores stdio de Python con configuración portable por espacio de trabajo, con degradación elegante ante fallos de conexión y sin requerir dependencias de Node.js.

#### Scenario: Inicio y descubrimiento
- **GIVEN** servidores MCP configurados
- **WHEN** se solicita inicializar MCP
- **THEN** se inicializan las conexiones disponibles y si un servidor falla, se registra una advertencia no bloqueante manteniendo las herramientas nativas operativas

#### Scenario: Sin configuración o configuración inválida
- **GIVEN** configuración ausente o JSON inválido
- **WHEN** se inicia la CLI
- **THEN** no se ejecutan comandos de configuración inválida y las herramientas nativas siguen disponibles
