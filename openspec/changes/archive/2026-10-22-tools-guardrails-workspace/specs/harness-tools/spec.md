# Spec Delta: harness-tools

## Purpose

Define y expone las 6 herramientas operativas del agente (read_file, write_file, edit_file, list_dir, run_command, search_code) con esquemas JSON Schema y truncado de seguridad.

## ADDED Requirements

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
