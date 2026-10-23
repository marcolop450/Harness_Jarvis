# Spec Delta: harness-tools

## ADDED Requirements

### Requirement: Integración de herramientas compatibles con Model Context Protocol (MCP)
El sistema SHALL soportar e integrar un mínimo de 3 herramientas o clientes bajo el estándar Model Context Protocol (MCP), permitiendo extender las capacidades del arnés hacia servicios contextuales externos y almacenamiento estructurado.

#### Scenario: Invocación de herramienta MCP de consulta contextual
- **GIVEN** una herramienta MCP habilitada en el catálogo (e.g. inspección git, lectura web/http o consulta sqlite)
- **WHEN** el modelo emite un tool_call compatible con la especificación MCP
- **THEN** el despachador ejecuta la herramienta a través del cliente MCP y retorna la salida truncada a 4000 caracteres

#### Scenario: Fallo o desconexión del servidor MCP
- **GIVEN** un fallo de conexión o error en el servicio MCP consultado
- **WHEN** la herramienta intenta procesar la petición
- **THEN** retorna un mensaje de error resiliente en texto sin romper el bucle del agente
