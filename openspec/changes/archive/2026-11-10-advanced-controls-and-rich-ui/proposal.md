# Proposal

## Why
El agente CLI de Harness Jarvis cuenta con una base operativa sólida, pero carece de controles dinámicos en caliente (modo arquitecto `/plan`, ajuste de `/steps`, política `/approval`) y diagnósticos de observabilidad (`/doctor`, `/tokens`, `/diff`, `/tree`, `/export`). Además, su interfaz en terminal de texto plano carece de autocompletado interactivo y de la ergonomía visual moderna característica de herramientas de referencia como Claude Code u OpenCode.

## What Changes
- **Comandos de control y observabilidad**:
  - `/plan`: Alterna entre modo Arquitecto (solo lectura y diseño de solución sin modificar archivos) y modo Actuador (ejecución completa y escritura).
  - `/steps`: Ajusta dinámicamente el límite de pasos por consulta sin reiniciar la sesión.
  - `/approval`: Conmuta entre confirmación humana interactiva obligatoria (`[s/n]`) y modo automático controlado.
  - `/doctor`: Diagnóstica latencia y salud del endpoint LLM activo y de los servidores MCP.
  - `/tokens`: Informa el uso aproximado de la ventana de contexto y tokens consumidos.
  - `/tree`: Imprime el árbol de directorios del espacio de trabajo ignorando carpetas excluidas.
  - `/diff`: Muestra las diferencias de líneas agregadas/eliminadas en archivos durante la sesión activa.
  - `/export`: Exporta el historial limpio de la sesión a un archivo Markdown.
- **Interfaz enriquecida (Rich & Prompt Toolkit)**:
  - Autocompletado interactivo al escribir `/` con ayuda contextual emergente.
  - Paneles, cajas y tablas con bordes Unicode redondeados (`╭─╮`) y jerarquía de color limpia.
  - Spinners y tarjetas compactas para ejecución de herramientas y llamadas al modelo.
  - Fallback transparente a texto plano si la terminal no es TTY.

## Capabilities

### Modified Capabilities
- `cli-entrypoint`: Incorpora autocompletado con `prompt_toolkit`, renderizado visual `rich`, y el catálogo de nuevos comandos de control y observabilidad.
- `agent-loop`: Admite límite dinámico de pasos por consulta y ejecución restringida a solo lectura en modo Arquitecto.
- `security-guardrails`: Permite alternar la política de confirmación interactiva en tiempo de ejecución vía `/approval`.

## Impact
- **Dependencias**: Incorporación de `rich` y `prompt-toolkit`.
- **Módulos**: `harness/agent_loop.py`, `harness/guardrails.py`, `harness/cli.py`, `main.py`.
- **Fuera de alcance**: Frameworks externos (LangChain/CrewAI), entornos gráficos web/GUI o servidores HTTP pesados.
