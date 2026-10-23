# harness-tools Specification

## Purpose
Define y expone las 6 herramientas operativas del agente (read_file, write_file, edit_file, list_dir, run_command, search_code) con esquemas JSON Schema y truncado de seguridad.

## Requirements

### Requirement: Definición estricta y catálogo de herramientas
El módulo tools SHALL exponer exactamente 6 herramientas compatibles con la especificación JSON Schema de OpenAI, categorizadas en niveles de riesgo AUTO y CONFIRM.

#### Scenario: Consulta del catálogo de herramientas
- **GIVEN** el módulo de herramientas inicializado
- **WHEN** se solicita la lista de especificaciones de herramientas para el LLM
- **THEN** retorna las 6 herramientas con esquemas válidos que detallan nombres, tipos y parámetros requeridos

### Requirement: Truncado preventivo a 4000 caracteres
Toda salida generada por cualquiera de las herramientas SHALL ser acotada a un máximo estricto de 4000 caracteres para preservar la ventana de contexto.

#### Scenario: Salida voluminosa de comando o lectura
- **GIVEN** un archivo o comando cuya salida excede los 4000 caracteres
- **WHEN** se ejecuta la herramienta correspondiente
- **THEN** la salida se trunca a 4000 caracteres y se anexa un pie informativo indicando el recorte

### Requirement: Resiliencia ante excepciones operativas
Las funciones de ejecución de herramientas SHALL capturar cualquier excepción del sistema operativo o parámetros erróneos y retornar un mensaje explicativo en texto.

#### Scenario: Edición con texto objetivo no coincidente
- **GIVEN** un archivo existente pero un parámetro target inexistente en el contenido
- **WHEN** se ejecuta edit_file
- **THEN** la herramienta retorna un mensaje de error descriptivo sin propagar excepciones que interrumpan el agente

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
