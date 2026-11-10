# Spec Delta: harness-tools

## MODIFIED Requirements

### Requirement: Truncado preventivo a 4000 caracteres
Toda salida de herramienta SHALL tener como máximo 4000 caracteres aplicando truncado inteligente Head+Tail que conserva los primeros 1000 caracteres y los últimos 3000 caracteres junto con un pie indicando los caracteres omitidos.

#### Scenario: Salida voluminosa de comando o lectura
- **GIVEN** una salida de herramienta que supera los 4000 caracteres
- **WHEN** se entrega el resultado al agente
- **THEN** se conservan los primeros 1000 caracteres y los últimos 3000 caracteres insertando una advertencia intermedia sin exceder el límite total

### Requirement: Resiliencia ante excepciones operativas
Las funciones de ejecución de herramientas SHALL capturar cualquier excepción del sistema operativo o parámetros erróneos y retornar un mensaje explicativo y de diagnóstico instructivo en texto.

#### Scenario: Edición con texto objetivo no coincidente
- **GIVEN** un archivo existente pero un parámetro target inexistente o repetido varias veces
- **WHEN** se ejecuta edit_file
- **THEN** la herramienta retorna un mensaje de error descriptivo indicando al modelo que use read_file para verificar las líneas exactas sin propagar excepciones fatales
