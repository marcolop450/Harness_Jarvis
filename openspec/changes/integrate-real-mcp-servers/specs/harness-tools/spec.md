## MODIFIED Requirements

### Requirement: Definición estricta y catálogo de herramientas
El módulo tools SHALL exponer las seis herramientas operativas y sqlite_query como herramientas nativas; el catálogo efectivo añade herramientas MCP descubiertas con nombres sin colisiones.

#### Scenario: Consulta del catálogo de herramientas
- **GIVEN** herramientas nativas y servidores disponibles
- **WHEN** se solicita el catálogo
- **THEN** retorna esquemas JSON válidos y nombres mcp_<servidor>__<herramienta> exclusivamente para llamadas MCP

#### Scenario: Migración de nombres
- **GIVEN** sesión guardada con nombres antiguos
- **WHEN** se reanuda
- **THEN** se conserva el historial y las nuevas llamadas usan nombres actuales, sin reejecutar herramientas históricas

### Requirement: Truncado preventivo a 4000 caracteres
Toda salida de herramienta SHALL tener como máximo 4000 caracteres incluyendo el pie informativo.

#### Scenario: Salida voluminosa de comando o lectura
- **GIVEN** salida mayor de 4000 caracteres
- **WHEN** se entrega al modelo
- **THEN** se recorta e incluye aviso sin exceder 4000

### Requirement: Integración de herramientas compatibles con Model Context Protocol (MCP)
El sistema SHALL integrar tres servidores MCP reales: Fetch, Git y Filesystem. Las funciones locales no cuentan como servidores MCP.

#### Scenario: Invocación de herramienta MCP de consulta contextual
- **GIVEN** servidor habilitado
- **WHEN** el modelo solicita una herramienta descubierta
- **THEN** el cliente envía una llamada MCP real y devuelve salida acotada

#### Scenario: Fallo o desconexión del servidor MCP
- **GIVEN** conexión fallida
- **WHEN** se solicita una herramienta MCP
- **THEN** se informa el fallo sin romper el bucle ni usar un sustituto local
