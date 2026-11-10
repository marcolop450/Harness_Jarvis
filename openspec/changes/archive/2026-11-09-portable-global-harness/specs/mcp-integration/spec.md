# Spec Delta: mcp-integration

## MODIFIED Requirements

### Requirement: Conexiones MCP reales y configuración portable
Jarvis SHALL conectar Fetch y Git mediante servidores stdio de Python resolviendo la configuración en cascada: workspace local, directorio global de usuario (`~/.harness/mcp.json`) o plantilla empaquetada, con degradación elegante ante fallos y sin dependencias de Node.js.

#### Scenario: Inicio y descubrimiento
- **GIVEN** servidores MCP configurados
- **WHEN** se solicita inicializar MCP
- **THEN** se inicializan las conexiones disponibles y si un servidor falla, se registra una advertencia no bloqueante manteniendo las herramientas nativas operativas

#### Scenario: Sin configuración o configuración inválida
- **GIVEN** configuración ausente o JSON inválido
- **WHEN** se inicia la CLI
- **THEN** no se ejecutan comandos de configuración inválida y las herramientas nativas siguen disponibles

#### Scenario: Fallback a configuración global en carpetas vírgenes
- **GIVEN** una carpeta de trabajo sin archivo `mcp.json` local
- **WHEN** el usuario inicia la CLI en esa carpeta
- **THEN** el sistema carga la configuración global de servidores MCP desde `~/.harness/mcp.json` o la inicializa desde la plantilla empaquetada, dejando disponibles las herramientas MCP
