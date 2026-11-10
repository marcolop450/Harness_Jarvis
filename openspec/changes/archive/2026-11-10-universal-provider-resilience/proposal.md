# Proposal: Resiliencia Universal de Proveedores y Sanitización de Entrada en CLI

## Motivation
1. **Evitar modelos fantasmas o no configurados al arrancar:** Si una sesión previa registró un modelo en la nube que carece de API Key en el entorno actual, el CLI no debe forzarlo como activo ni bloquear al usuario con avisos sobre proveedores no deseados.
2. **Soporte universal para IA Local y APIs de Nube:** Facilitar el uso directo de servidores locales (Ollama, LM Studio, vLLM, servidores custom) sin requerir claves de API artificiales, y soportar proveedores populares adicionales (DeepSeek, etc.).
3. **Tolerancia a copia de prompt en la terminal:** Si el usuario copia un comando con el prefijo de la consola (ej. `jarvis> /endpoint ...` o `> /model ...`), el sistema debe sanitizar la entrada y reconocer el comando en lugar de enviarlo erróneamente como un prompt al modelo.

## Scope
- Sanitización de prefijos de entrada (`jarvis>`, `>`, `$`) en el REPL de `main.py`.
- Detección de claves en `has_valid_key_for_provider`: los proveedores locales (`ollama`, `lmstudio`, `local`, `custom`) o aquellos con endpoint en `localhost`/`127.0.0.1` no requieren API Key.
- Extensión de `SUPPORTED_PROVIDERS` en `harness/llm_provider.py` para incluir `lmstudio`, `local`, `custom`, y `deepseek`.
- En `_run_repl`, si el modelo activo recuperado de la memoria requiere clave pero está ausente y no es local, no dejarlo como activo en caliente (mostrar `[sin configurar]` con guía clara).
