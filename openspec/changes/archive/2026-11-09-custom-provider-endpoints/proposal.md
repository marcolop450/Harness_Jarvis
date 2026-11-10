# Propuesta: Configuración Dinámica de Endpoints para Proveedores

## Por qué
Actualmente, los proveedores locales o compatibles con OpenAI asumen puertos fijos (ej. Ollama en `11434`), lo que provoca fallos de conexión cuando el usuario ejecuta servidores en otras direcciones o puertos (ej. LM Studio en `1234`, vLLM en `8000`, o servidores en red local). El sistema debe solicitar o permitir configurar la dirección/endpoint dinámicamente para operar con cualquier servidor.

## Qué Cambiará
- **Soporte de URL en `/model add`:** Permitir especificar la URL del endpoint directamente al registrar un modelo: `/model add <proveedor> <modelo> [endpoint_url]`.
- **Nuevo comando `/endpoint`:** Permitir ver y cambiar la URL base de cualquier proveedor en caliente: `/endpoint <proveedor> [nueva_url]` con solicitud interactiva si no se suministra la URL.
- **Persistencia de Endpoints Personalizados:** Guardar las URLs configuradas en el archivo de memoria de modelos (`endpoints` en `.harness_models.json` / `~/.harness/models.json`) y en variables `<PROV>_BASE_URL`.
- **Diagnóstico Amigable ante Errores de Conexión:** Si falla la conexión a un proveedor, informar la URL exacta a la que se intentó conectar y sugerir el comando para corregir el endpoint (`/endpoint <prov> <url>`).

## Capacidades

### Nuevas Capacidades
*(Ninguna; se refinan capacidades existentes).*

### Capacidades Modificadas
- `multi-api-provider`: Soporte para resolver y priorizar URLs base dinámicas configuradas por el usuario por proveedor.
- `workspace-context`: Incorporación del comando `/endpoint` y soporte de argumento de URL en `/model add`.

## Impacto
- **Archivos afectados:** `harness/llm_provider.py`, `harness/model_config.py`, `main.py`.
- **Compatibilidad:** 100% retrocompatible. Si no se especifica endpoint, se conservan los valores predeterminados existentes.
