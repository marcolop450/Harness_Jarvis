# Design: Volcado Inmediato de Confirmación y Guía Interactiva Fuera de Línea

## Context
En Windows, cuando `input()` recibe cadenas multilínea con caracteres especiales, el búfer de consola se retrasa hasta que se presiona Enter. Además, la coincidencia estricta en `confirm_action` rechaza respuestas con pulsación doble (`ss`) o tildes (`sí`). Por otro lado, no existía un comando de guía predeterminado que explique a un nuevo usuario el ciclo de trabajo de la herramienta sin necesitar acceso a internet o un modelo de IA activo.

## Goals / Non-Goals

**Goals:**
- Separar el despliegue visual de la advertencia de seguridad del prompt de captura en `confirm_action`: imprimir los detalles mediante `print(..., flush=True)` y ejecutar `sys.stdout.flush()`.
- Flexibilizar la respuesta afirmativa en `confirm_action` para aceptar `s`, `si`, `sí`, `ss`, `y`, `yes`, o cualquier cadena que empiece por `s` o `y`.
- Crear una función `print_user_guide()` en `main.py` invocable con `/guide`, `/guia` y `/help` que explique de forma didáctica y visual todo el flujo de trabajo (claves, modelos, instrucciones, confirmaciones y limpieza), operativa 100% en local.

**Non-Goals:**
- No implementar tutoriales por pasos bloqueantes o interfaces wizard complejas que impidan usar comandos regulares.

## Decisions

### 1. Volcado explícito antes de la captura de confirmación
- **Decisión**:
  ```python
  sys.stdout.flush()
  print("\n+--------------------------------------------------------+", flush=True)
  print(f"| [CONFIRMACION REQUERIDA]", flush=True)
  print(f"| Accion: {action_description}", flush=True)
  if details:
      print(f"| Detalles: {details}", flush=True)
  print("+--------------------------------------------------------+", flush=True)
  sys.stdout.flush()
  answer = prompter("¿Desea autorizar esta operacion? [s/n]: ").strip().lower()
  ```
- **Razón**: Garantiza que el búfer de salida de Windows se vacíe en la pantalla inmediatamente antes de que el proceso se detenga a esperar la interacción del usuario.

### 2. Tolerancia a respuestas afirmativas
- **Decisión**: Reconocer cualquier respuesta cuyo inicio sea `s` o `y`, o que coincida con `sí`, `si`, `ss`, `yes`, `ok`.
- **Razón**: Evita cancelaciones accidentales por pulsación rápida o doble tecla en la consola.

### 3. Guía interactiva fuera de línea
- **Decisión**: Implementar `print_user_guide()` en `main.py` y vincularla a `/guide`, `/guia` y `/help` en `handle_slash_command`.
- **Razón**: Permite a cualquier usuario recién llegado entender el sistema y comenzar a trabajar sin necesidad de tener una API configurada ni gastar tokens.

## Risks / Trade-offs

- **[Falsos positivos en confirmación]** → Una respuesta no deseada que empiece con `s` podría interpretarse como positiva.
  *Mitigación*: Se exige confirmación interactiva explícita; rechazar explícitamente palabras como `salir` o `stop` si fuera necesario, aunque en un prompt `[s/n]` escribir texto ajeno es infrecuente.
