# Spec Delta: workspace-context

## MODIFIED Requirements

### Requirement: Comando interactivo de selección de modelo
La interfaz CLI SHALL permitir al usuario consultar y cambiar el proveedor o modelo activo dinámicamente mediante el comando /model, registrar endpoints personalizados con /endpoint o en /model add, y persistir dichas configuraciones.

#### Scenario: Cambio de modelo en caliente
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario ejecuta el comando '/model gemini gemini-2.5-flash'
- **THEN** el sistema actualiza el proveedor y modelo para las consultas subsiguientes y notifica el cambio

#### Scenario: Registro de modelo con endpoint personalizado
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario ejecuta '/model add ollama qwen/qwen3.5-9b http://localhost:1234/v1'
- **THEN** el sistema registra el modelo y configura el endpoint específico para ese proveedor en la memoria persistente

#### Scenario: Configuración interactiva de endpoint con /endpoint
- **GIVEN** una sesión activa en la terminal
- **WHEN** el usuario ejecuta el comando '/endpoint ollama http://localhost:1234/v1'
- **THEN** el sistema actualiza la dirección base del proveedor y la persiste para las sesiones subsiguientes
