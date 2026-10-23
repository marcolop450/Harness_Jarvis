---
trigger: always_on
---

# Harness Constitution

## 1. Fórmula del Sistema
El diseño y la implementación del sistema se rigen de manera obligatoria por la siguiente arquitectura:
**Harness = Modelo (Adaptador Multi-API) + Reglas (System Prompt y Guardrails) + Contexto (Árbol de carpetas y AGENT.md) + Herramientas (6 tools con JSON Schema)**

## 2. Separación Estricta de Módulos (`harness/`)
Toda la lógica central del agente CLI debe organizarse exclusivamente en 4 módulos dentro del directorio `harness/`:
- `llm_provider.py`: Único archivo autorizado para conectar e interactuar con APIs externas de modelos de lenguaje.
- `agent_loop.py`: Ciclo de ejecución principal `while` con límite estricto de pasos `MAX_STEPS = 15`.
- `tools.py`: Definición y ejecución de las 6 herramientas del agente con esquemas JSON Schema y salidas truncadas estrictamente a 4000 caracteres.
- `guardrails.py`: Mecanismos de seguridad y validación:
  - Bloqueo total de lectura y modificación de archivos `.env` y archivos confidenciales.
  - Validación de rutas para restringir todas las operaciones dentro del directorio de trabajo actual (`cwd`).
  - Confirmación interactiva obligatoria del usuario `[s/n]` antes de editar/crear archivos o ejecutar comandos de consola.

## 3. Disciplina OpenSpec
- **No escribir código sin tarea activa**: Está terminantemente prohibido generar, modificar o refactorizar código de la aplicación si no corresponde a una tarea explícita y activa en `tasks.md`.
- **Ejecución atómica**: Abordar y ejecutar exactamente una tarea a la vez.
- **Validación continua**: Probar y verificar cada tarea de forma exhaustiva antes de marcarla como completada con `[x]`.
