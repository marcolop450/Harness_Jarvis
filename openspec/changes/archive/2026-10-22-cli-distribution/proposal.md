# Proposal

## Why
Actualmente el agente sólo puede ejecutarse invocando `python main.py` desde la raíz del repositorio. Para ofrecer una experiencia CLI estándar instalable con un solo comando en cualquier PC con Windows desde CMD o PowerShell, se requiere empaquetar el proyecto registrando el comando de consola global `jarvis` y proveer un script de instalación automatizado.

## What Changes
- Creación de `pyproject.toml` conforme a PEP 518/621 registrando el punto de entrada de consola `jarvis = "main:main"`.
- Creación de script automatizado `install.bat` para Windows que comprueba Python/pip, instala el paquete en modo editable (`pip install -e .`) y verifica la disponibilidad de `jarvis`.
- Adición de pruebas de verificación para la metadata del empaquetado y la invocación del punto de entrada.
- **Fuera de alcance**: Publicación en el índice público PyPI, compilación a binario monolítico (.exe vía PyInstaller) o modificaciones a la lógica interna de los 4 módulos de `harness/`.

## Capabilities

### New Capabilities
- `cli-distribution`: Empaquetado estandarizado con comando global `jarvis` e instalador automatizado para Windows.

### Modified Capabilities
<!-- Ninguna capacidad existente modifica sus requerimientos funcionales. -->

## Impact
- Nuevos archivos en la raíz: `pyproject.toml`, `install.bat`.
- Dependencias de instalación: `setuptools >= 61.0`.
- Sistemas: Consola CMD y PowerShell en Windows con Python 3.10+.
