# Tasks: core-multi-api-loop

## 1. Entorno y Estructura Base

- [x] 1.1 Configurar dependencias del proyecto en `requirements.txt` (incluyendo `openai` y `python-dotenv`) y verificar instalación ejecutando un chequeo de importación.
- [x] 1.2 Crear el paquete `harness/` con su archivo `__init__.py` y verificar que la estructura modular queda registrada en el directorio.

## 2. Adaptador Multi-API (`harness/llm_provider.py`)

- [x] 2.1 Definir las estructuras de datos `NormalizedResponse` y `NormalizedToolCall` en `harness/llm_provider.py` y verificar su instanciación y tipado mediante pruebas unitarias.
- [x] 2.2 Implementar la resolución de credenciales y `base_url` para OpenAI, Gemini, Groq, OpenRouter y Ollama local en `harness/llm_provider.py`, verificando la selección por entorno y parámetros con tests unitarios.
- [x] 2.3 Implementar la función `call_llm` con el cliente unificado de OpenAI y normalización robusta de `content` y `tool_calls` (parseo seguro de JSON), verificando su comportamiento con tests que utilicen mocks de respuestas.

## 3. Bucle de Control Reactivo (`harness/agent_loop.py`)

- [x] 3.1 Implementar el bucle `run_agent_loop` en `harness/agent_loop.py` gestionando el historial de mensajes y la llamada a `call_llm`.
- [x] 3.2 Implementar la condición de parada por respuesta final y el límite estricto inamovible de `MAX_STEPS = 15`, verificando con tests simulados que el ciclo nunca excede los 15 pasos.

## 4. Punto de Entrada CLI y Verificación Integrada

- [x] 4.1 Implementar `main.py` con interfaz interactiva en terminal (banner inicial, prompt para el usuario, comandos de salida 'exit' / 'quit').
- [x] 4.2 Integrar `main.py` con `run_agent_loop` y verificar el flujo end-to-end simulado en consola.
