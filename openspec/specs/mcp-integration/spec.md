# mcp-integration Specification

## Purpose
Conectar Jarvis con servidores MCP externos mediante un ciclo de vida controlado y herramientas verificables, conservando la disponibilidad de la CLI.

## Requirements

### Requirement: Conexiones MCP reales y configuración portable
Jarvis SHALL conectar Fetch, Git y Filesystem mediante stdio con configuración por espacio de trabajo, sin descargas al iniciar.

#### Scenario: Inicio y descubrimiento
- **GIVEN** dependencias instaladas y configuración válida
- **WHEN** se solicita MCP
- **THEN** se inicializan conexiones y se descubren todas las páginas de herramientas habilitadas

#### Scenario: Sin configuración o configuración inválida
- **GIVEN** configuración ausente o JSON inválido
- **WHEN** se inicia la CLI
- **THEN** no se ejecutan comandos de configuración inválida y las herramientas nativas siguen disponibles

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
