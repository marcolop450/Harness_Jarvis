# Design: core-multi-api-loop

## Context

El proyecto se inicia sin base de código previa. Para cumplir con la Constitución del Harness, la lógica debe dividirse estrictamente en módulos dentro de `harness/`. Este cambio establece el punto de entrada CLI y los dos primeros componentes estructurales: `harness/llm_provider.py` y `harness/agent_loop.py`.

## Goals / Non-Goals

**Goals:**
- Proporcionar un punto de entrada CLI en terminal (`main.py`) que ofrezca un bucle de interacción de comandos con el usuario.
- Implementar `harness/llm_provider.py` como único cliente de red para APIs de LLM utilizando la especificación OpenAI (`base_url` + `api_key`) para conectar OpenAI, Gemini, Groq, OpenRouter y Ollama local.
- Definir estructuras de datos para `NormalizedResponse` y `NormalizedToolCall`.
- Implementar `harness/agent_loop.py` con ciclo de control reactivo `while` restringido a `MAX_STEPS = 15`.

**Non-Goals:**
- Implementar las 6 herramientas definitivas en `harness/tools.py` (se mantendrán stubs o listas vacías hasta el siguiente cambio).
- Implementar las validaciones completas de `harness/guardrails.py`.
- Persistir sesiones en base de datos o almacenamiento secundario.

## Decisions

### Decisión 1: Cliente unificado compatible con OpenAI SDK
- **Elección**: Usar el cliente estándar de OpenAI parametrizando `base_url` y `api_key` para todos los proveedores.
- **Alternativas**: Instalar SDKs específicos por proveedor (`google-generativeai`, `groq`, etc.).
- **Razón**: Mantiene dependencias mínimas, reduce la superficie de código y aprovecha que los proveedores modernos exponen endpoints compatibles con OpenAI Chat Completions.

### Decisión 2: Contrato normalizado de salida (`NormalizedResponse`)
- **Elección**: Desacoplar el bucle de ejecución de los objetos nativos del SDK mediante `NormalizedResponse` y `NormalizedToolCall`.
- **Razón**: Permite que `agent_loop.py` trabaje con estructuras predecibles e independientes de cómo cada proveedor serialice los argumentos en `function.arguments`.

### Decisión 3: Estricta restricción de `MAX_STEPS = 15`
- **Elección**: Limitar el bucle `while` en `agent_loop.py` a 15 pasos máximos por turno.
- **Razón**: Previene recursión descontrolada, consumo innecesario de cuota y loops infinitos si el modelo no converge.

## Risks / Trade-offs

- **Riesgo**: Variaciones en el soporte de Function Calling en modelos locales de Ollama.
  - **Mitigación**: Manejo defensivo en la normalización de argumentos JSON con captura de errores.
- **Riesgo**: Falta de credenciales en variables de entorno.
  - **Mitigación**: Verificación temprana y mensajes de error orientados a indicar la variable faltante.
