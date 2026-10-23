---
name: multi-api-adapter
description: Instrucciones y mejores prácticas para construir y mantener el adaptador multi-proveedor en harness/llm_provider.py usando un cliente unificado compatible con OpenAI, soportando múltiples proveedores y normalizando tool_calls.
---

# Multi-API Adapter Skill

Esta habilidad guía la implementación, configuración y pruebas del módulo [harness/llm_provider.py](file:///d:/Harness%20Jarvis/harness/llm_provider.py).

## Principios Fundamentales
1. **Punto Único de Conexión**: Ningún otro archivo del proyecto debe importar SDKs de LLM ni conectarse a redes o APIs de modelos de lenguaje. Todo el tráfico hacia los LLMs pasa exclusivamente por `llm_provider.py`.
2. **Compatibilidad Estándar OpenAI**: Utilizar la interfaz y especificación de OpenAI Chat Completions (`base_url` + `api_key`) para conectarse a cualquier proveedor compatible sin requerir dependencias fragmentadas.
3. **Normalización Total**: Independientemente del proveedor (Gemini, Groq, OpenRouter, OpenAI, Ollama), la salida del proveedor debe normalizarse en una estructura uniforme antes de llegar a `agent_loop.py`.

---

## Proveedores y Configuración

El adaptador debe soportar de forma nativa la resolución de `base_url` y `api_key` para los siguientes proveedores:

| Proveedor | Variable de Entorno | `base_url` por defecto | Modelo recomendado por defecto |
| :--- | :--- | :--- | :--- |
| **OpenAI** | `OPENAI_API_KEY` | `https://api.openai.com/v1` | `gpt-4o-mini` / `gpt-4o` |
| **Gemini** | `GEMINI_API_KEY` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` |
| **Groq** | `GROQ_API_KEY` | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| **OpenRouter** | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct` |
| **Ollama (Local)** | *(Opcional)* | `http://localhost:11434/v1` | `qwen2.5-coder:7b` |

### Resolución Automática o Explícita
- Permitir seleccionar el proveedor mediante argumento de CLI o variable de entorno (ej. `HARNESS_PROVIDER=gemini`).
- Si no se especifica, detectar automáticamente el primer proveedor que tenga su respectiva API key configurada en el entorno.

---

## Normalización de Respuestas y `tool_calls`

Diferentes proveedores o versiones de modelos pueden entregar argumentos de herramientas como strings JSON, objetos o formatos ligeramente divergentes. `llm_provider.py` debe garantizar una estructura estricta:

```python
# Estructura normalizada esperada por agent_loop.py
class NormalizedResponse:
    content: str | None
    tool_calls: list[NormalizedToolCall]
    finish_reason: str

class NormalizedToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
```

### Reglas de Parseo y Manejo de Errores en `tool_calls`
1. **Parseo de Argumentos**:
   - Intentar siempre parsear `function.arguments` con `json.loads()`.
   - Si `arguments` ya es un `dict`, mantenerlo intacto.
   - Si el JSON es inválido o viene truncado por el modelo, capturar el error y proporcionar un diccionario de contingencia o un argumento `raw_args` para que el agente loop pueda reportar el fallo al modelo sin romperse.
2. **Formato de Herramientas Enviadas (`tools`)**:
   - Exponer las herramientas en formato compatible con OpenAI Tools (`{"type": "function", "function": {...}}`).

---

## Verificación del Módulo
Para validar `llm_provider.py`:
- Crear pruebas unitarias con mock de respuestas para validar que la normalización de `tool_calls` funciona idénticamente con payloads simulados de OpenAI, Gemini, Groq y Ollama.
- Comprobar que variables inexistentes o conexiones caídas arrojen excepciones claras de configuración o conectividad.
