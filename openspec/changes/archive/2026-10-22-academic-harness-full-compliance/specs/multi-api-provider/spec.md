# Spec Delta: multi-api-provider

## MODIFIED Requirements

### Requirement: Manejo de errores de conexión y credenciales
El adaptador SHALL capturar fallos de autenticación, límites de cuota (Rate Limit 429) o problemas de red del proveedor y transformarlos en mensajes de error humanos limpios y categorizados por código de estado, sin volcar diccionarios JSON crudos.

#### Scenario: Clave de API no configurada
- **GIVEN** un entorno donde no hay variables de clave para el proveedor solicitado
- **WHEN** se intenta realizar una llamada al modelo
- **THEN** el sistema arroja una excepción informativa indicando la variable de entorno requerida

#### Scenario: Exceso de cuota o límite de tokens (Error 429)
- **GIVEN** una llamada al modelo rechazada por límite de tokens por minuto (OTPM/TPM)
- **WHEN** el adaptador captura la excepción de la API
- **THEN** formatea un mensaje limpio indicando el código 429 y sugiriendo esperar o cambiar de modelo con /model, sin exponer JSONs crudos

#### Scenario: Fallo de autenticación o modelo no disponible (401 / 404)
- **GIVEN** una respuesta de error 401 o 404 por parte del proveedor externo
- **WHEN** el adaptador procesa el error
- **THEN** devuelve un mensaje comprensible indicando la causa específica (clave inválida o modelo inexistente) de forma concisa
