# Proposal: core-multi-api-loop

## Why
Para construir un asistente CLI autónomo tipo Claude Code, es necesario establecer la infraestructura fundamental: la interfaz de terminal interactiva, el adaptador de modelos desacoplado y el ciclo central de control que gestione el flujo de pasos sin incurrir en bucles infinitos.

## What Changes
- Punto de entrada CLI en terminal para recibir instrucciones del usuario y proyectar la salida del agente.
- Módulo `harness/llm_provider.py` como único conector hacia APIs externas, compatible con OpenAI, Gemini, Groq, OpenRouter y Ollama local, normalizando respuestas y `tool_calls`.
- Módulo `harness/agent_loop.py` que implementa el ciclo de ejecución `while` con límite estricto de `MAX_STEPS = 15`.
- **Fuera de alcance**:
  - Implementación de las 6 herramientas completas en `harness/tools.py`.
  - Mecanismos de seguridad y confirmación interactiva en `harness/guardrails.py`.
  - Persistencia de sesiones en bases de datos o disco.

## Capabilities

### New Capabilities
- `cli-entrypoint`: Interfaz de línea de comandos interactiva para recibir prompts del usuario y mostrar respuestas.
- `multi-api-provider`: Adaptador unificado compatible con la API de OpenAI para conectar Gemini, Groq, OpenRouter y Ollama local con normalización de respuestas.
- `agent-loop`: Ciclo reactivo `while` con límite estricto `MAX_STEPS = 15` para orquestar el razonamiento y la terminación controlada del agente.

### Modified Capabilities
*(Ninguna; proyecto inicial).*

## Impact
- Establece la estructura base del proyecto y el núcleo de ejecución en `harness/`.
- Dependencias mínimas requeridas: `openai` (o cliente HTTP compatible) y carga de variables de entorno.
