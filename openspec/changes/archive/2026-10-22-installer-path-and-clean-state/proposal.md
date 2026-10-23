# Proposal

## Why
Cuando un nuevo usuario instala el agente en Windows, la carpeta `Scripts` de Python no siempre está en el PATH, requiriendo configuración manual propensa a errores. Además, al iniciar por primera vez sin credenciales, el banner asumía Gemini por defecto en lugar de mostrar un estado limpio `[SIN CONFIGURAR]`.

## What Changes
- Automatización en `install.bat` e `install.ps1` para detectar la ruta de `Scripts` de Python y añadirla automáticamente al `PATH` de usuario de Windows de forma permanente y segura.
- Actualización del PATH en la sesión activa de consola dentro del instalador para que `jarvis` funcione inmediatamente sin reiniciar la terminal.
- Actualización de `harness/model_config.py` y `main.py` para presentar `[SIN CONFIGURAR]` en proveedor y modelo cuando no existan credenciales ni configuración previa.
- Manejo amigable en la CLI guiando al usuario a usar `/key` o `/model` si envía una consulta sin proveedor configurado.
- **Fuera de alcance**: Modificaciones a los guardrails o a las 6 herramientas en `harness/tools.py`.

## Capabilities

### New Capabilities
<!-- No se introducen nuevas capacidades independientes. -->

### Modified Capabilities
- `cli-distribution`: Automatizar el registro de la ruta Scripts en el PATH del usuario durante la instalación.
- `cli-entrypoint`: Mostrar estado inicial `[SIN CONFIGURAR]` y orientar al usuario antes de su primera configuración.

## Impact
- Módulos afectados: `install.bat`, `install.ps1`, `harness/model_config.py`, `main.py` y pruebas asociadas.
- Compatibilidad: Windows CMD y PowerShell sin dependencias externas adicionales.
