# Proposal: Cumplimiento Académico Total del Arnés y Optimización de Errores

## Why
El informe académico de clase establece directrices y exigencias rigurosas para la defensa individual del proyecto: mínimo 3 MCPs (Model Context Protocol), subagentes especializados con contexto aislado (Figura 1 del PDF), gestión y listado de sesiones (`/sessions`, `/resume`), compactación inteligente de historial (`/compact`), y un manejo de errores limpio y comprensible que elimine los volcados crudos de JSON (como el error 429 de tokens o 401 de autenticación), además de evitar la repetición molesta de autorizaciones para un mismo archivo.

## What Changes
- **Mapeador Universal de Errores Limpios**: Transforma excepciones crudas en mensajes cortos, claros y de una sola línea (`[Error 429 - Límite de Tokens/Cuota]`, `[Error 401 - Clave Inválida]`, `[Error 404]`, `[Error 500]`).
- **Control de Tokens y Parámetro `max_tokens`**: Ajuste inteligente para evitar rebasar límites OTPM en tiers gratuitos de proveedores como Groq.
- **Autorización Fluida por Lote (`[s/n/a]`)**: Añade opción `a` (*Autorizar todo*) para recordar la aprobación del archivo durante el turno activo sin repetición innecesaria.
- **Compactación Inteligente de Contexto (`/compact`)**: Resumen semántico del historial con LLM para reducir el consumo de tokens y preservar la precisión.
- **Gestión Completa de Sesiones (`/sessions` y `/resume <id>`)**: Listado de sesiones previas con fecha/hora y reanudación interactiva.
- **Subagente Aislado de Investigación**: Capacidad de delegar tareas exploratorias en modo solo lectura con contexto limpio, retornando únicamente un resumen final al orquestador.
- **Integración de Mínimo 3 Servidores/Tools MCP**: Soporte nativo para el protocolo Model Context Protocol (MCP).
- **Manual de Defensa Técnica (`DEFENSA_HARNESS.md`)**: Guía de dominio conceptual para la evaluación individual.

## Capabilities

### Modified Capabilities
- `multi-api-provider`: Manejo unificado de códigos de error HTTP y control preventivo de tokens de salida.
- `security-guardrails`: Soporte para autorización por lote `[s/n/a]` en el turno activo.
- `workspace-context`: Comando de compactación inteligente (`/compact`) y catálogo/listado de sesiones históricas (`/sessions`, `/resume`).
- `agent-loop`: Medición de tiempos de ejecución y delegación a subagente con contexto aislado.
- `harness-tools`: Soporte e integración de 3 herramientas/servidores bajo el protocolo Model Context Protocol (MCP).

## Impact
- Actualizaciones en `harness/llm_provider.py`, `harness/guardrails.py`, `harness/agent_loop.py`, `harness/tools.py`, `harness/model_config.py` y `main.py`.
- Fuera de alcance: Interfaces web gráficas pesadas (mantiene arquitectura CLI pura).
