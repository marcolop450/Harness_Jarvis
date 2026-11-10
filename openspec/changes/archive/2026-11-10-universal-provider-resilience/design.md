# Design: Resiliencia Universal de Proveedores y Sanitización de Entrada en CLI

## 1. Sanitización de Entrada en REPL
En `main.py`, en el bucle principal de lectura:
```python
raw_input = input(prompt_symbol).strip()
cleaned = raw_input
for pfx in ("jarvis>", "jarvis >", ">", "$"):
    if cleaned.lower().startswith(pfx):
        cleaned = cleaned[len(pfx):].strip()
```
Toda la lógica de comandos slash y envío de mensajes evaluará `cleaned`. Esto evita que comandos pegados con `jarvis> /endpoint ...` se interpreten como preguntas al LLM.

## 2. Soporte Universal de Proveedores Locales y Nube
En `harness/llm_provider.py`:
- `SUPPORTED_PROVIDERS`:
  - `openai`, `gemini`, `groq`, `openrouter`, `ollama` (existentes)
  - `lmstudio` (base_url: `http://localhost:1234/v1`, default_model: `default`)
  - `local` (base_url: `http://localhost:1234/v1`, default_model: `default`)
  - `custom` (base_url: `http://localhost:8000/v1`, default_model: `default`)
  - `deepseek` (base_url: `https://api.deepseek.com/v1`, default_model: `deepseek-chat`)
- En `resolve_provider`:
  - Si el proveedor es local (`ollama`, `lmstudio`, `local`, `custom`) o su `base_url` apunta a `localhost` o `127.0.0.1`, y `api_key` está vacía, se asigna automáticamente `"local"` como dummy key sin lanzar excepción.

## 3. Verificación de Claves Inteligente
En `has_valid_key_for_provider(provider)` en `main.py`:
- Retornar `True` inmediatamente para proveedores locales (`ollama`, `lmstudio`, `local`, `custom`) o cuando la URL base configurada apunte a `localhost` o `127.0.0.1`.
- Para proveedores de nube, validar la variable de entorno correspondiente.

## 4. Estado Inicial sin Proveedor Fantasma
En `_run_repl`:
- Si el proveedor cargado de memoria requiere clave obligatoria y dicha clave no existe en el entorno, deseleccionar el proveedor activo (`active_provider = None`, `active_model = None`) y mostrar el banner `[sin configurar]`, guiando al usuario para que configure su proveedor deseado (local o nube).
