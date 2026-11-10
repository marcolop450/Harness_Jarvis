# Spec Delta: multi-api-provider

## MODIFIED Requirements

### Requirement: Normalización de respuestas y tool_calls
El adaptador SHALL procesar la respuesta cruda del modelo y transformarla en una estructura uniforme con contenido textual y lista normalizada de tool_calls, auto-reparando JSONs mal formados o retornando un error estructurado no fatal al bucle de ejecución.

#### Scenario: Respuesta estándar de texto
- **GIVEN** una respuesta del modelo sin llamadas a herramientas
- **WHEN** el adaptador normaliza la respuesta
- **THEN** devuelve un objeto con el texto en el campo content y una lista vacía de tool_calls

#### Scenario: Normalización de tool_calls con argumentos JSON
- **GIVEN** una respuesta del modelo con una o más llamadas a funciones con argumentos serializados en JSON
- **WHEN** el adaptador procesa los tool_calls
- **THEN** devuelve los tool_calls normalizados con id, name y arguments parseados como diccionario

#### Scenario: Auto-reparación de JSON defectuoso en llamadas a herramientas
- **GIVEN** una llamada a función con argumentos JSON que contienen comillas sin escapar o sintaxis imperfecta
- **WHEN** el adaptador intenta deserializar los argumentos
- **THEN** aplica una rutina de saneamiento y reparación de JSON retornando los argumentos reparados o un error descriptivo estructurado sin terminar el proceso

### Requirement: Manejo de errores de conexión y credenciales
El adaptador SHALL capturar fallos de autenticación, límites de cuota (Rate Limit 429) o problemas de red del proveedor, aplicando reintentos con Exponential Backoff ante errores 429 y transformando fallos definitivos en mensajes limpios de una línea.

#### Scenario: Clave de API no configurada
- **GIVEN** un entorno donde no hay variables de clave para el proveedor solicitado
- **WHEN** se intenta realizar una llamada al modelo
- **THEN** el sistema arroja una excepción informativa indicando la variable de entorno requerida

#### Scenario: Exceso de cuota o límite de tokens (Error 429)
- **GIVEN** una llamada al modelo rechazada por límite de tokens por minuto (OTPM/TPM)
- **WHEN** el adaptador captura el error 429
- **THEN** aplica una espera exponencial con aviso visual en consola y reintenta la llamada antes de fallar de manera definitiva

#### Scenario: Fallo de autenticación o modelo no disponible (401 / 404)
- **GIVEN** una respuesta de error 401 o 404 por parte del proveedor externo
- **WHEN** el adaptador procesa el error
- **THEN** devuelve un mensaje comprensible indicando la causa específica (clave inválida o modelo inexistente) de forma concisa
