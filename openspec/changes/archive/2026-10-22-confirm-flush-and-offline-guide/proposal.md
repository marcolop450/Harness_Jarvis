# Proposal: Volcado Inmediato de Confirmación y Guía Interactiva Fuera de Línea

## Why
Actualmente en consolas de Windows, las solicitudes de confirmación interactiva `[s/n]` sufren retrasos de dibujo en pantalla porque `input()` retiene el búfer hasta que se presiona Enter, haciendo que el usuario cancele por accidente. Además, respuestas con doble pulsación involuntaria (`ss`) o tildes (`sí`) son rechazadas indebidamente. Por otra parte, nuevos usuarios que inician la aplicación sin claves ni modelos no disponen de una guía predeterminada dentro de la terminal que les enseñe a trabajar offline y paso a paso.

## What Changes
- **Volcado inmediato y libre de bloqueos en confirmación**: Se imprimen los detalles de la acción con `flush=True` antes de invocar `input()`, garantizando que el mensaje de confirmación aparezca al instante en Windows.
- **Tolerancia y resiliencia en respuestas afirmativas**: Acepta `s`, `si`, `sí`, `ss`, `y`, `yes` o cualquier respuesta afirmativa natural.
- **Guía interactiva integrada (`/guide`, `/guia`, `/help`)**: Comando local que muestra una guía visual estructurada para nuevos usuarios, operativa 100% sin conexión a internet, sin API keys y sin requerir IA.

## Capabilities

### Modified Capabilities
- `security-guardrails`: Volcado inmediato y garantizado en terminal de la solicitud interactiva `[s/n]` con evaluación tolerante de respuestas afirmativas.
- `cli-entrypoint`: Soporte para comandos de guía interactiva local (`/guide`, `/guia`, `/help`) operativos sin necesidad de proveedor de IA.

## Impact
- Afecta a `harness/guardrails.py` y `main.py`.
- No introduce librerías externas adicionales.
- Fuera de alcance: Modales gráficos en navegadores o interfaces web GUI.
