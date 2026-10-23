# Design

## Context
Actualmente los scripts de instalación solo emiten una advertencia si la carpeta `Scripts` de Python no está en el PATH, obligando al usuario a intervenir manualmente. Por otro lado, `harness/model_config.py` asumía `gemini` y `gemini-2.5-flash` de manera predeterminada incluso cuando no existía ninguna clave de API ni selección previa, lo cual generaba confusión en usuarios nuevos.

## Goals / Non-Goals

**Goals:**
- Modificar `install.bat` e `install.ps1` para que detecten automáticamente la ruta de scripts de Python (`sysconfig.get_path('scripts')`) y la agreguen al PATH de usuario en el Registro de Windows de forma permanente usando la API .NET de PowerShell (evitando el límite de 1024 caracteres de `setx`).
- Actualizar el PATH de la sesión de consola activa para que `jarvis` funcione de inmediato sin reiniciar la terminal.
- Ajustar `harness/model_config.py` para devolver valores vacíos o nulos cuando no haya memoria de modelos ni claves en `.env`.
- Actualizar `main.py` para renderizar `[SIN CONFIGURAR]` en el banner y prompt, y orientar al usuario con un mensaje instructivo si intenta enviar una consulta sin proveedor configurado.
- Actualizar la suite de pruebas unitarias para validar el estado no configurado.

**Non-Goals:**
- Modificar la lógica interna de los 4 módulos de ejecución de herramientas o el bucle del agente.
- Modificar la memoria persistente cuando el usuario ya ha configurado un modelo explícito con `/model`.

## Decisions

### 1. Inyección de PATH en Windows mediante API .NET de PowerShell
- **Decisión**: En `install.bat` e `install.ps1`, invocar:
  `[Environment]::SetEnvironmentVariable('Path', ..., 'User')`
- **Razón**: El comando clásico `setx.exe` trunca variables a 1024 caracteres y copia variables del sistema al ámbito de usuario. La API .NET modifica estrictamente la clave `HKEY_CURRENT_USER\Environment\Path` sin truncado y sin riesgos.

### 2. Estado no configurado explícito en `model_config.py`
- **Decisión**: `load_model_memory()` no asumirá Gemini por defecto si el archivo `.harness_models.json` no existe o no tiene selección activa y no hay claves en `.env`. Retornará `(None, None)` o strings vacíos.
- **Razón**: Claridad y transparencia total para el usuario desde el primer inicio.

### 3. Manejo de consultas en estado no configurado en `main.py`
- **Decisión**: Si el usuario escribe una instrucción cuando el proveedor es nulo o vacío, el REPL emitirá una guía amigable:
  `[Aviso]: No tienes ningún proveedor configurado. Usa /key <proveedor> <clave> o /model ollama <modelo> para comenzar.`
- **Razón**: Previene excepciones no controladas y llamadas de red fallidas.

## Risks / Trade-offs

- **[Riesgo] La ejecución de scripts de PowerShell está restringida por ExecutionPolicy en algunas máquinas**  
  → *Mitigación*: Invocar PowerShell siempre con `-ExecutionPolicy Bypass -NoProfile`.
- **[Riesgo] Actualización de PATH en procesos padres**  
  → *Mitigación*: `install.bat` actualiza la variable en el Registro para futuras consolas y hace `set PATH=%PATH%;...` para la sesión local actual.
