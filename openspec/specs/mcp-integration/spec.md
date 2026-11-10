# mcp-integration Specification

## Purpose
Conectar Jarvis con servidores MCP externos mediante un ciclo de vida controlado y herramientas verificables, conservando la disponibilidad de la CLI.

## Requirements

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

### Requirement: Despacho y ciclo de vida resilientes
Jarvis SHALL ejecutar herramientas por MCP, conservar conexiones por sesión y cerrar procesos al salir; conexión y llamadas tienen límite predeterminado de 30 segundos.

#### Scenario: Llamada real
- **GIVEN** servidor conectado
- **WHEN** el modelo solicita su herramienta
- **THEN** se envía tools/call y se añade su resultado al historial con trazabilidad de servidor y herramienta

#### Scenario: Fallo y recuperación
- **GIVEN** servidor ausente, desconectado o lento
- **WHEN** falla una conexión o llamada
- **THEN** se informa el error, se limita la espera y se permite reconectar sin fallback local

#### Scenario: Cierre
- **GIVEN** conexiones abiertas
- **WHEN** el usuario sale o interrumpe
- **THEN** se cierran clientes y procesos sin quedar hilos de MCP activos
