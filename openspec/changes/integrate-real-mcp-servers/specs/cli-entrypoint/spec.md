## ADDED Requirements

### Requirement: Inspección y reconexión MCP
La CLI SHALL admitir /mcp y /mcp reconnect, mostrando estado, errores y herramientas habilitadas sin requerir un modelo configurado.

#### Scenario: Inspección
- **GIVEN** CLI abierta
- **WHEN** se ejecuta /mcp
- **THEN** se muestran los servidores y herramientas realmente disponibles

#### Scenario: Reconexión
- **GIVEN** servidor fallido
- **WHEN** se ejecuta /mcp reconnect
- **THEN** se reintenta su conexión y se actualiza su estado

### Requirement: MCP en ambos modos de ejecución
La CLI SHALL suministrar el mismo catálogo MCP y políticas al REPL y al modo -p.

#### Scenario: Solicitud directa
- **GIVEN** MCP configurado
- **WHEN** se inicia con -p
- **THEN** el modelo puede usar MCP y los procesos se cierran al concluir
