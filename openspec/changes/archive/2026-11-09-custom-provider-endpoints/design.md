# Diseño Técnico: Configuración Dinámica de Endpoints para Proveedores

## Contexto
Los modelos locales o autohospedados (LM Studio, Ollama, vLLM, LocalAI) se ejecutan en diferentes puertos (`1234`, `11434`, `8000`) o en máquinas remotas en la red local. Actualmente Jarvis requiere que el usuario conozca y defina variables de entorno a mano para cambiar la URL base de un proveedor.

## Metas / No Metas

**Metas:**
- Permitir al usuario definir la dirección del servidor directamente en `/model add <prov> <modelo> [url]`.
- Añadir el comando slash `/endpoint [prov] [url]` para consultar y cambiar URLs de servidores locales o proxies en caliente.
- Persistir los endpoints por proveedor en la memoria de modelos (`.harness_models.json` / `~/.harness/models.json`) bajo el campo `"endpoints"`.
- Diagnosticar claramente los errores de conexión informando la URL exacta que falló y sugiriendo cómo reconfigurarla.

**No Metas:**
- No modificar el protocolo de invocación OpenAI ni el formato de `tool_calls`.

## Decisiones Técnicas

### 1. Extensión del Esquema de Memoria de Modelos (`.harness_models.json`)
Se añade el campo `"endpoints"` al JSON de memoria:
```json
{
  "active_provider": "ollama",
  "active_model": "qwen/qwen3.5-9b",
  "endpoints": {
    "ollama": "http://localhost:1234/v1"
  },
  "saved_models": { ... }
}
```
Al resolver el proveedor en `resolve_provider(prov)` o al cargar el REPL, se consulta este diccionario y se aplica en `os.environ[f"{prov.upper()}_BASE_URL"]` si existe.

### 2. Sintaxis de `/model add`
- `/model add <prov> <mod> [url]`
- Si se suministra `[url]`, se valida sintaxis básica (`http://` o `https://`) y se guarda en `"endpoints"` para ese proveedor.

### 3. Comando `/endpoint`
- `/endpoint`: Lista los proveedores soportados y sus endpoints actuales (indicando si es personalizado o predeterminado).
- `/endpoint <prov> <url>`: Asigna la nueva dirección, la guarda y actualiza `os.environ[f"{prov.upper()}_BASE_URL"]`.
- `/endpoint <prov>`: Prompt interactivo: `Ingrese la URL del endpoint para <prov>: `.

### 4. Diagnóstico de Error de Conexión
Al capturar `APIConnectionError` o fallo de red en `llm_provider.py` o `main.py`:
`[Error de Conexión]: No se pudo contactar a '{provider}' en {base_url}.`
`Sugerencia: Si el servidor está en otro puerto o máquina, configúralo con /endpoint {provider} <url>`
